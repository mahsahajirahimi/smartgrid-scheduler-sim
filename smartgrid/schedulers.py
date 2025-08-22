from typing import Optional
from .models import Request

class BaseScheduler:
    name = "base"
    def push(self, rq: Request):
        raise NotImplementedError
    def pop(self, now: float) -> Optional[Request]:
        raise NotImplementedError
    def __len__(self):
        raise NotImplementedError

class FIFOScheduler(BaseScheduler):
    name = "FIFO"
    def __init__(self):
        self._heap = []
        self._ctr = 0
    def push(self, rq: Request):
        heapq.heappush(self._heap, (rq.arrival_time, self._ctr, rq))
        self._ctr += 1
    def pop(self, now: float) -> Optional[Request]:
        if not self._heap: return None
        return heapq.heappop(self._heap)[2]
    def __len__(self):
        return len(self._heap)

class NPPSScheduler(BaseScheduler):
    name = "NPPS"
    def __init__(self):
        self._heap = []
        self._ctr = 0
    def push(self, rq: Request):
        heapq.heappush(self._heap, (-rq.priority, rq.arrival_time, self._ctr, rq))
        self._ctr += 1
    def pop(self, now: float) -> Optional[Request]:
        if not self._heap: return None
        return heapq.heappop(self._heap)[3]
    def __len__(self):
        return len(self._heap)

class EDFScheduler(BaseScheduler):
    name = "EDF"
    def __init__(self):
        self._heap = []
        self._ctr = 0
    def push(self, rq: Request):
        heapq.heappush(self._heap, (rq.deadline, rq.arrival_time, self._ctr, rq))
        self._ctr += 1
    def pop(self, now: float) -> Optional[Request]:
        if not self._heap: return None
        return heapq.heappop(self._heap)[3]
    def __len__(self):
        return len(self._heap)

class WRRScheduler(BaseScheduler):
    name = "WRR"
    def __init__(self, weights=None):
        self.weights = weights or {"A": 1, "B": 1}
        self.queues = {g: [] for g in self.weights}
        self.round_robin = []
        for g, w in self.weights.items():
            self.round_robin += [g]*int(max(1, w))
        self.rr_idx = 0
        self._ctr = 0
    def push(self, rq: Request):
        self.queues.setdefault(rq.group, [])
        self.queues[rq.group].append((rq.arrival_time, self._ctr, rq))
        self._ctr += 1
    def pop(self, now: float) -> Optional[Request]:
        if sum(len(q) for q in self.queues.values()) == 0:
            return None
        tried = 0
        while tried < len(self.round_robin):
            g = self.round_robin[self.rr_idx % len(self.round_robin)]
            self.rr_idx += 1
            tried += 1
            if self.queues.get(g) and len(self.queues[g]) > 0:
                self.queues[g].sort(key=lambda x: (x[0], x[1]))
                return self.queues[g].pop(0)[2]
        for g, q in self.queues.items():
            if q:
                q.sort(key=lambda x: (x[0], x[1]))
                return q.pop(0)[2]
        return None
    def __len__(self):
        return sum(len(q) for q in self.queues.values())


import heapq

class WRR_EDF_Scheduler(BaseScheduler):
    name = "WRR+EDF"
    def __init__(self, weights=None):
        # weights: dict group -> weight (int>=1)
        self.weights = {g: int(max(1, w)) for g, w in (weights or {"A":2, "B":1}).items()}
        self.heaps = {g: [] for g in self.weights}   # group -> heap of (deadline, arrival_time, id, rq)
        self.round = []
        for g, w in self.weights.items():
            self.round += [g] * w
        self.rr_idx = 0
        self._ctr = 0

    def push(self, rq: Request):
        g = rq.group
        if g not in self.heaps:
            self.heaps[g] = []
            self.weights[g] = 1
            self.round.append(g)
        heapq.heappush(self.heaps[g], (rq.deadline, rq.arrival_time, self._ctr, rq))
        self._ctr += 1

    def pop(self, now: float) -> Optional[Request]:
        if self.__len__() == 0:
            return None
        tried = 0
        L = len(self.round)
        while tried < L:
            g = self.round[self.rr_idx % L]
            self.rr_idx += 1
            tried += 1
            if self.heaps[g]:
                return heapq.heappop(self.heaps[g])[3]
        for g, h in self.heaps.items():
            if h:
                return heapq.heappop(h)[3]
        return None

    def __len__(self):
        return sum(len(h) for h in self.heaps.values())


class WRR_NPPS_Scheduler(BaseScheduler):
    name = "WRR+NPPS"
    def __init__(self, weights=None):
        self.weights = {g: int(max(1, w)) for g, w in (weights or {"A":2, "B":1}).items()}
        self.heaps = {g: [] for g in self.weights}   # group -> heap of (-priority, arrival_time, id, rq)
        self.round = []
        for g, w in self.weights.items():
            self.round += [g] * w
        self.rr_idx = 0
        self._ctr = 0

    def push(self, rq: Request):
        g = rq.group
        if g not in self.heaps:
            self.heaps[g] = []
            self.weights[g] = 1
            self.round.append(g)
        heapq.heappush(self.heaps[g], (-rq.priority, rq.arrival_time, self._ctr, rq))
        self._ctr += 1

    def pop(self, now: float) -> Optional[Request]:
        if self.__len__() == 0:
            return None
        tried = 0
        L = len(self.round)
        while tried < L:
            g = self.round[self.rr_idx % L]
            self.rr_idx += 1
            tried += 1
            if self.heaps[g]:
                return heapq.heappop(self.heaps[g])[3]
        for g, h in self.heaps.items():
            if h:
                return heapq.heappop(h)[3]
        return None

    def __len__(self):
        return sum(len(h) for h in self.heaps.values())
