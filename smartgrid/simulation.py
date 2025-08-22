import heapq, math, random
from typing import Dict, List, Tuple, Optional
from .models import Request, Consumer

class SmartGridSim:
    def __init__(
        self,
        scheduler,
        T: float = 1000.0,
        seed: int = 42,
        chi: float = 0.8,       # arrival rate (Poisson)
        lam1: float = 1.5,      # controller processing rate (Exp)
        lam2: float = 0.5,      # renewable/battery processing rate (Exp)
        overhead_C: float = 0.2,
        dispatch_probs: Dict[str, float] = None,  # {'renewable':0.6, 'battery':0.2, 'nonrenewable':0.2}
        deadline_scale: float = 5.0,
        n_consumers: int = 6,
        expire_on_deadline: bool = True,
        record_timeline: bool = True,
        outage_rate: Dict[str, float] = None,       # Poisson rate for outage starts
        outage_mean_duration: Dict[str, float] = None,  # mean duration for outages
    ):
        self.scheduler = scheduler
        self.T = T
        self.rng = random.Random(seed)
        self.chi = chi
        self.lam1 = lam1
        self.lam2 = lam2
        self.overhead_C = overhead_C
        self.dispatch_probs = dispatch_probs or {'renewable':0.6, 'battery':0.2, 'nonrenewable':0.2}
        s = sum(self.dispatch_probs.values())
        self.dispatch_probs = {k: v/s for k, v in self.dispatch_probs.items()}
        self.deadline_scale = deadline_scale
        self.n_consumers = n_consumers

        self.expire_on_deadline = expire_on_deadline
        self.record_timeline = record_timeline

        self.sources = ["renewable", "battery", "nonrenewable"]
        self.outage_rate = outage_rate or {"renewable": 0.002, "battery": 0.001}  # per time-unit
        self.outage_mean_duration = outage_mean_duration or {"renewable": 30.0, "battery": 20.0}

        # state
        self.now = 0.0
        self.events: List[Tuple[float,int,str,Optional[object]]] = []
        self._eid = 0
        self.busy = False
        self.in_service: Optional[Tuple[object,float]] = None
        self.req_counter = 0

        # metrics (totals)
        self.wait_times: List[float] = []
        self.service_times: List[float] = []
        self.response_times: List[float] = []
        self.usage_counts = {'renewable':0, 'battery':0, 'nonrenewable':0}
        self.busy_time = 0.0
        self.last_busy_change = 0.0
        self.queue_timeline: List[Tuple[float,int]] = []

        # per-priority/group stats
        self.by_priority = {}
        self.by_group = {}

        # deadline miss drops
        self.deadline_drops = 0

        #outage state & metrics
        self.available = {k: True for k in self.sources}
        self.outage_count = {k: 0 for k in self.sources}
        self.outage_time = {k: 0.0 for k in self.sources}
        self._outage_started_at = {k: None for k in self.sources}
        self.reroute_due_outage = 0  # how many times preferred source was unavailable

        self.consumers = [Consumer(consumer_id=i) for i in range(n_consumers)]

    def _exp(self, rate: float) -> float:
        if rate <= 0: return float('inf')
        u = self.rng.random()
        return -math.log(1 - u) / rate

    def _exp_mean(self, mean: float) -> float:
        if mean <= 0: return 0.0
        u = self.rng.random()
        return -math.log(1 - u) * mean

    def _choice_available(self, probs: Dict[str, float]) -> str:
        eff = {k: p for k, p in probs.items() if self.available.get(k, True) and p > 0}
        if not eff:
            return "nonrenewable"
        tot = sum(eff.values())
        u = self.rng.random() * tot
        cum = 0.0
        for k, p in eff.items():
            cum += p
            if u <= cum:
                return k
        return list(eff.keys())[-1]

    def _schedule(self, t: float, kind: str, payload=None):
        if t <= self.T:
            heapq.heappush(self.events, (t, self._eid, kind, payload))
            self._eid += 1

    def initialize(self):
        self.now = 0.0
        self.busy = False
        self.in_service = None
        self.events.clear()
        self._eid = 0
        self.req_counter = 0

        self.wait_times.clear()
        self.service_times.clear()
        self.response_times.clear()
        self.usage_counts = {k:0 for k in self.usage_counts}
        self.busy_time = 0.0
        self.last_busy_change = 0.0
        self.queue_timeline.clear()
        self.by_priority.clear()
        self.by_group.clear()
        self.deadline_drops = 0
        self.available = {k: True for k in self.sources}
        self.outage_count = {k: 0 for k in self.sources}
        self.outage_time = {k: 0.0 for k in self.sources}
        self._outage_started_at = {k: None for k in self.sources}
        self.reroute_due_outage = 0

        # first arrival
        self._schedule(self._exp(self.chi), 'arrival', None)
        if self.record_timeline:
            self.queue_timeline.append((0.0, 0))

        # schedule initial outage starts for each configured source
        for src, rate in self.outage_rate.items():
            t_start = self._exp(rate)
            self._schedule(t_start, 'outage_start', src)


    def _handle_arrival(self):
        cid = self.rng.randrange(self.n_consumers)
        self.req_counter += 1
        demand = max(0.1, self.rng.gauss(1.0, 0.3))
        priority = 1 + int(self.rng.random() * 3)  # 1..3
        deadline = self.now + max(0.1, self._exp_mean(self.deadline_scale))
        rq = Request(
            req_id=self.req_counter,
            consumer_id=cid,
            arrival_time=self.now,
            demand=demand,
            priority=priority,
            deadline=deadline,
            group=('A' if cid % 2 == 0 else 'B')
        )
        self.scheduler.push(rq)
        if self.record_timeline:
            self.queue_timeline.append((self.now, len(self.scheduler)))

        next_arrival = self.now + self._exp(self.chi)
        self._schedule(next_arrival, 'arrival', None)

        if not self.busy:
            self._start_service()

    def _start_service(self):
        rq = self.scheduler.pop(self.now)
        if rq is None:
            return

        # deadline expiration check
        if self.expire_on_deadline and self.now > rq.deadline:
            self.deadline_drops += 1
            if self.record_timeline:
                self.queue_timeline.append((self.now, len(self.scheduler)))
            self._start_service()
            return

        # choose source
        chosen = self._choice_available(self.dispatch_probs)
        rq.chosen_source = chosen

        if not self.available.get(chosen, True):
            self.reroute_due_outage += 1

        # start serving
        self.busy = True
        self.last_busy_change = self.now
        rq.start_service_time = self.now

        controller_proc = self._exp(self.lam1)
        source_proc = self._exp(self.lam2) if chosen in ('renewable', 'battery') else 0.0
        service_time = controller_proc + self.overhead_C + source_proc

        finish = self.now + service_time
        self.in_service = (rq, service_time)
        self._schedule(finish, 'departure', rq)
        if self.record_timeline:
            self.queue_timeline.append((self.now, len(self.scheduler)))

    def _handle_departure(self, rq: Request):
        if self.busy:
            self.busy_time += (self.now - self.last_busy_change)
        self.busy = False

        rq.finish_time = self.now
        wait = (rq.start_service_time - rq.arrival_time) if rq.start_service_time is not None else 0.0
        service_time = self.in_service[1] if self.in_service else 0.0
        response = rq.finish_time - rq.arrival_time

        self.wait_times.append(wait)
        self.service_times.append(service_time)
        self.response_times.append(response)
        if rq.chosen_source:
            self.usage_counts[rq.chosen_source] = self.usage_counts.get(rq.chosen_source, 0) + 1

        p = rq.priority
        dpp = self.by_priority.setdefault(p, {"wait_sum":0.0, "resp_sum":0.0, "n":0})
        dpp["wait_sum"] += wait; dpp["resp_sum"] += response; dpp["n"] += 1
        g = rq.group
        dpg = self.by_group.setdefault(g, {"wait_sum":0.0, "resp_sum":0.0, "n":0})
        dpg["wait_sum"] += wait; dpg["resp_sum"] += response; dpg["n"] += 1

        self.in_service = None
        self._start_service()

    def _handle_outage_start(self, src: str):
        if self.available.get(src, True):
            self.available[src] = False
            self.outage_count[src] = self.outage_count.get(src, 0) + 1
            self._outage_started_at[src] = self.now
            dur = self._exp_mean(self.outage_mean_duration.get(src, 10.0))
            self._schedule(self.now + dur, 'outage_end', src)
        rate = self.outage_rate.get(src, 0.0)
        t_next = self.now + self._exp(rate)
        self._schedule(t_next, 'outage_start', src)

    def _handle_outage_end(self, src: str):
        if not self.available.get(src, True):
            self.available[src] = True
            started = self._outage_started_at.get(src, None)
            if started is not None:
                self.outage_time[src] += (self.now - started)
            self._outage_started_at[src] = None

    def run(self):
        self.initialize()
        while self.events:
            t, eid, kind, payload = heapq.heappop(self.events)
            self.now = t
            if self.now > self.T:
                break
            if kind == 'arrival':
                self._handle_arrival()
            elif kind == 'departure':
                self._handle_departure(payload)  # payload=Request
            elif kind == 'outage_start':
                self._handle_outage_start(payload)  # payload=src
            elif kind == 'outage_end':
                self._handle_outage_end(payload)    # payload=src

        if self.busy:
            self.busy_time += max(0.0, self.T - self.last_busy_change)

        for src, t0 in self._outage_started_at.items():
            if t0 is not None:
                self.outage_time[src] += max(0.0, self.T - t0)

        n = len(self.response_times)
        avg_wait = sum(self.wait_times)/n if n>0 else 0.0
        avg_resp = sum(self.response_times)/n if n>0 else 0.0
        util = self.busy_time / max(1e-9, self.T)
        total = sum(self.usage_counts.values()) or 1
        mix = {k: v/total for k,v in self.usage_counts.items()}

        by_priority_mean = {
            p: {
                "avg_wait": (d["wait_sum"]/d["n"]) if d["n"] else 0.0,
                "avg_response": (d["resp_sum"]/d["n"]) if d["n"] else 0.0,
                "n": d["n"]
            } for p, d in sorted(self.by_priority.items())
        }
        by_group_mean = {
            g: {
                "avg_wait": (d["wait_sum"]/d["n"]) if d["n"] else 0.0,
                "avg_response": (d["resp_sum"]/d["n"]) if d["n"] else 0.0,
                "n": d["n"]
            } for g, d in sorted(self.by_group.items())
        }

        return {
            "processed": n,
            "avg_wait": avg_wait,
            "avg_response": avg_resp,
            "utilization": util,
            "energy_mix": mix,
            "queue_timeline": self.queue_timeline if self.record_timeline else [],
            "drops_deadline": self.deadline_drops,
            "by_priority": by_priority_mean,
            "by_group": by_group_mean,
            "outage_count": self.outage_count,
            "outage_time": self.outage_time,        # total down-time per source
            "reroute_due_outage": self.reroute_due_outage,
            "availability": {k: 1.0 - (self.outage_time.get(k,0.0)/max(self.T,1e-9)) for k in self.sources},
        }
