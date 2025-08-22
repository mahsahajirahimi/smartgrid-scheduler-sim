import matplotlib.pyplot as plt
import numpy as np
from smartgrid.schedulers import FIFOScheduler, NPPSScheduler, EDFScheduler, WRRScheduler
from smartgrid.simulation import SmartGridSim

def run_one(sched, **kw):
    sim = SmartGridSim(scheduler=sched, **kw)
    return sim.run()

def sweep_load(chis, T=1000.0, seed=123):
    sched_factories = {
        "FIFO": lambda: FIFOScheduler(),
        "NPPS": lambda: NPPSScheduler(),
        "EDF":  lambda: EDFScheduler(),
        "WRR":  lambda: WRRScheduler(weights={"A":2, "B":1}),
    }
    results = {name: [] for name in sched_factories}
    for chi in chis:
        for name, fac in sched_factories.items():
            out = run_one(
                fac(),
                T=T,
                seed=seed,
                chi=chi,
                lam1=1.5,
                lam2=0.5,
                overhead_C=0.2,
                dispatch_probs={'renewable':0.6, 'battery':0.2, 'nonrenewable':0.2},
                deadline_scale=5.0,
                n_consumers=6,
                expire_on_deadline=True,
                record_timeline=False,
            )
            results[name].append(out)
    return results

def plot_metric_vs_load(chis, results, metric_key="avg_wait", title=None, ylabel=None):
    plt.figure()
    for name, outs in results.items():
        ys = [o[metric_key] for o in outs]
        plt.plot(chis, ys, marker="o", label=name)
    plt.xlabel("Arrival rate χ")
    plt.ylabel(ylabel or metric_key)
    plt.title(title or f"{metric_key} vs Load")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

def main():
    scheds = [("FIFO", FIFOScheduler()), ("NPPS", NPPSScheduler()), ("EDF", EDFScheduler()), ("WRR", WRRScheduler(weights={"A":2,"B":1}))]
    for name, s in scheds:
        res = run_one(
            s, T=1000.0, seed=123, chi=0.8, lam1=1.5, lam2=0.5, overhead_C=0.2,
            dispatch_probs={'renewable':0.6, 'battery':0.2, 'nonrenewable':0.2},
            deadline_scale=5.0, n_consumers=6, expire_on_deadline=True
        )
        print(f"== {name} ==")
        print(f"processed={res['processed']}, drops_deadline={res['drops_deadline']}")
        print(f"avg_wait={res['avg_wait']:.3f}, avg_response={res['avg_response']:.3f}, utilization={res['utilization']:.3f}")
        print("by_priority:", res["by_priority"])
        print("by_group   :", res["by_group"])
        print("energy_mix :", res["energy_mix"])
        print()

    chis = np.linspace(0.4, 1.2, 5)
    results = sweep_load(chis, T=1000.0, seed=321)

    plot_metric_vs_load(chis, results, metric_key="avg_wait", title="Average Wait vs Load", ylabel="Avg Wait (time)")
    plot_metric_vs_load(chis, results, metric_key="avg_response", title="Average Response vs Load", ylabel="Avg Response (time)")

    # Optional: deadline drops vs load (only meaningful when expire_on_deadline=True)
    plt.figure()
    for name, outs in results.items():
        ys = [o["drops_deadline"] for o in outs]
        plt.plot(chis, ys, marker="o", label=name)
    plt.xlabel("Arrival rate χ")
    plt.ylabel("Deadline drops (count)")
    plt.title("Deadline Drops vs Load")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.show()

if __name__ == "__main__":
    main()
