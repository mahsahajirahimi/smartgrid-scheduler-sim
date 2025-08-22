import matplotlib.pyplot as plt
from copy import deepcopy

from smartgrid.simulation import SmartGridSim
from smartgrid.schedulers import (
    FIFOScheduler, NPPSScheduler, EDFScheduler, WRRScheduler,
    WRR_EDF_Scheduler, WRR_NPPS_Scheduler
)

def make_sim(sched, with_outage=False):
    kw = dict(
        T=1000.0, seed=123, chi=0.8, lam1=1.5, lam2=0.5, overhead_C=0.2,
        dispatch_probs={'renewable':0.6, 'battery':0.2, 'nonrenewable':0.2},
        deadline_scale=5.0, n_consumers=6, expire_on_deadline=True, record_timeline=False
    )
    if with_outage:
        kw.update(outage_rate={"renewable": 0.004, "battery": 0.002},
                  outage_mean_duration={"renewable": 25.0, "battery": 15.0})
    else:
        kw.update(outage_rate={}, outage_mean_duration={})
    return SmartGridSim(scheduler=sched, **kw)

def clone_scheduler_for_outage(sched):
    cls = sched.__class__
    if hasattr(sched, "weights"):
        return cls(weights=deepcopy(getattr(sched, "weights")))
    return cls()

def run_one(name, sched, with_outage=False):
    sim = make_sim(sched, with_outage=with_outage)
    res = sim.run()
    print(f"== {name} ({'Outages' if with_outage else 'No Outage'}) ==")
    print(f"processed={res['processed']}, drops_deadline={res['drops_deadline']}")
    print(f"avg_wait={res['avg_wait']:.3f}, avg_response={res['avg_response']:.3f}, utilization={res['utilization']:.3f}")
    print("energy_mix:", res["energy_mix"])
    print("by_priority:", res["by_priority"])
    print()
    return res

def main():
    scheds = [
        ("FIFO", FIFOScheduler()),
        ("NPPS", NPPSScheduler()),
        ("EDF",  EDFScheduler()),
        ("WRR",  WRRScheduler(weights={"A":2,"B":1})),
        ("WRR+EDF",  WRR_EDF_Scheduler(weights={"A":2,"B":1})),
        ("WRR+NPPS", WRR_NPPS_Scheduler(weights={"A":2,"B":1})),
    ]

    base, outg = {}, {}

    for name, s in scheds:
        base[name] = run_one(name, s, with_outage=False)

    for name, s in scheds:
        s2 = clone_scheduler_for_outage(s)
        outg[name] = run_one(name, s2, with_outage=True)

    names = [n for n, _ in scheds]
    x = list(range(len(names)))
    w = 0.38

    plt.figure(figsize=(9,5))
    plt.bar([i - w/2 for i in x], [base[n]["avg_wait"] for n in names], width=w, label="No Outage")
    plt.bar([i + w/2 for i in x], [outg[n]["avg_wait"] for n in names], width=w, label="With Outages")
    plt.xticks(x, names, rotation=20)
    plt.ylabel("Avg Wait")
    plt.title("Average Wait: Classical vs Combined Schedulers")
    plt.legend()
    plt.tight_layout()

    plt.figure(figsize=(9,5))
    plt.bar([i - w/2 for i in x], [base[n]["drops_deadline"] for n in names], width=w, label="No Outage")
    plt.bar([i + w/2 for i in x], [outg[n]["drops_deadline"] for n in names], width=w, label="With Outages")
    plt.xticks(x, names, rotation=20)
    plt.ylabel("Deadline Drops")
    plt.title("Deadline Drops Comparison")
    plt.legend()
    plt.tight_layout()

    plt.show()

if __name__ == "__main__":
    main()
