import matplotlib.pyplot as plt
from smartgrid.schedulers import FIFOScheduler, NPPSScheduler, EDFScheduler, WRRScheduler
from smartgrid.simulation import SmartGridSim

def run_case(with_outage: bool, scheduler_name="FIFO"):
    sched = {
        "FIFO": FIFOScheduler,
        "NPPS": NPPSScheduler,
        "EDF":  EDFScheduler,
        "WRR":  lambda: WRRScheduler(weights={"A":2,"B":1}),
    }[scheduler_name]()
    kw = dict(
        T=1000.0, seed=123, chi=0.8, lam1=1.5, lam2=0.5, overhead_C=0.2,
        dispatch_probs={'renewable':0.6, 'battery':0.2, 'nonrenewable':0.2},
        deadline_scale=5.0, n_consumers=6, expire_on_deadline=True, record_timeline=False
    )
    if with_outage:
        kw.update(
            outage_rate={"renewable": 0.004, "battery": 0.002},
            outage_mean_duration={"renewable": 25.0, "battery": 15.0},
        )
    else:
        kw.update(outage_rate={}, outage_mean_duration={})

    sim = SmartGridSim(scheduler=sched, **kw)
    return sim.run()

def bar_compare(title, labels, base_vals, outage_vals, ylabel):
    x = list(range(len(labels)))
    w = 0.35
    plt.figure()
    plt.bar([i - w/2 for i in x], base_vals, width=w, label="No Outage")
    plt.bar([i + w/2 for i in x], outage_vals, width=w, label="With Outages")
    plt.xticks(x, labels)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.tight_layout()

def run_all():
    names = ["FIFO", "NPPS", "EDF", "WRR"]
    base = {}
    outg = {}
    for n in names:
        base[n] = run_case(False, scheduler_name=n)
        outg[n] = run_case(True, scheduler_name=n)

    # 1) Avg wait
    bar_compare(
        "Average Wait (No Outage vs With Outages)",
        names,
        [base[n]["avg_wait"] for n in names],
        [outg[n]["avg_wait"] for n in names],
        "Avg Wait (time)"
    )

    # 2) Processed
    bar_compare(
        "Processed Requests",
        names,
        [base[n]["processed"] for n in names],
        [outg[n]["processed"] for n in names],
        "Count"
    )

    # 3) Energy mix
    bar_compare(
        "Renewable Share",
        names,
        [base[n]["energy_mix"]["renewable"] for n in names],
        [outg[n]["energy_mix"]["renewable"] for n in names],
        "Share"
    )

    # 4) Availability
    for n in names:
        print(f"== {n} ==")
        print("No Outage -> availability:", base[n].get("availability", {}))
        print("With Outages -> availability:", outg[n].get("availability", {}))
        print("Outage counts:", outg[n].get("outage_count", {}))
        print("Outage time:", outg[n].get("outage_time", {}))
        print("Reroutes due to outage:", outg[n].get("reroute_due_outage", 0))
        print("avg_wait Δ:", outg[n]["avg_wait"] - base[n]["avg_wait"])
        print("renewable_share Δ:", outg[n]["energy_mix"]["renewable"] - base[n]["energy_mix"]["renewable"])
        print()

    plt.show()

if __name__ == "__main__":
    run_all()
