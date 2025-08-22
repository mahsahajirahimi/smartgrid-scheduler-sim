import matplotlib.pyplot as plt
from smartgrid.schedulers import FIFOScheduler, NPPSScheduler, EDFScheduler, WRRScheduler
from smartgrid.simulation import SmartGridSim

def run_demo():
    results = {}
    for name, sched in [
        ("FIFO", FIFOScheduler()),
        ("NPPS", NPPSScheduler()),
        ("EDF",  EDFScheduler()),
        ("WRR",  WRRScheduler(weights={"A":2, "B":1})),
    ]:
        sim = SmartGridSim(
            scheduler=sched,
            T=1000.0,
            seed=123,
            chi=0.8,
            lam1=1.5,
            lam2=0.5,
            overhead_C=0.2,
            dispatch_probs={'renewable':0.6, 'battery':0.2, 'nonrenewable':0.2},
            deadline_scale=5.0,
            n_consumers=6,
        )
        res = sim.run()
        results[name] = res
        print(f"== {name} == ")
        print(f"processed: {res['processed']}")
        print(f"avg_wait: {res['avg_wait']:.3f}, avg_response: {res['avg_response']:.3f}")
        print(f"utilization: {res['utilization']:.3f}")
        print(f"energy mix: {res['energy_mix']}")
        print()

    fifo_res = results["FIFO"]
    times = [t for (t, q) in fifo_res["queue_timeline"]]
    qlens = [q for (t, q) in fifo_res["queue_timeline"]]
    plt.figure()
    plt.step(times, qlens, where="post")
    plt.xlabel("Time")
    plt.ylabel("Queue length (FIFO)")
    plt.title("Queue Length Over Time (FIFO)")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_demo()
