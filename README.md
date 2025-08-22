# SmartGrid Scheduling Simulator

A discrete-event simulator for **Smart Grid scheduling** with multiple policies, deadlines, and source outages.  

---

## Features
- **Schedulers**: FIFO, NPPS, EDF, WRR, WRR+EDF, WRR+NPPS  
- **Deadlines & Drops**: requests expire if not served before deadline  
- **Outages**: random outages for renewable/battery; reports availability and downtime  
- **Metrics**: avg_wait, avg_response, utilization, energy_mix, per-priority/group  

---

## Installation
```bash
git clone https://github.com/<your-username>/smartgrid-scheduler-sim.git
cd smartgrid-scheduler-sim
pip install -r requirements.txt

```

# SmartGrid Scheduler Simulation

## How to Run

### 1. Quick Demo
```bash
python -m smartgrid.demo_run
```
- Prints scheduler stats  
- Shows FIFO queue length plot  

<img width="640" height="480" alt="Figure_1.1" src="https://github.com/user-attachments/assets/68ad4e37-6f5d-47b8-93da-62370e8a9921" />


---

### 2. Experiments – Load Sweep
```bash
python -m smartgrid.experiments
```
- Compares schedulers across arrival rates  
- Generates plots:  
  - Average Wait vs Load  
  - Average Response vs Load  
  - Deadline Drops vs Load  

<img width="640" height="480" alt="Figure_2.1" src="https://github.com/user-attachments/assets/9c092cf4-bc14-4c49-b30e-6385c342114c" />
<img width="640" height="480" alt="Figure_2.2" src="https://github.com/user-attachments/assets/2d706a29-9d83-4134-a0fc-5dd3b313031e" />
<img width="640" height="480" alt="Figure_2.3" src="https://github.com/user-attachments/assets/e35124bc-fc78-434b-a197-00e46642ed07" />


---

### 3. Experiments – Outages
```bash
python -m smartgrid.experiments_outages
```
- Runs schedulers with and without outages  
- Plots:  
  - Average Wait (bar)  
  - Processed Requests (bar)  
  - Renewable Share (bar)  
- Console: availability, outage counts, reroutes  

<img width="640" height="480" alt="Figure_3.1" src="https://github.com/user-attachments/assets/35220872-128c-48cb-bc3b-ea1947367c30" />
<img width="640" height="480" alt="Figure_3 2" src="https://github.com/user-attachments/assets/7cc09396-386b-4464-8fb7-71bff43f3837" />
<img width="640" height="480" alt="Figure_3 3" src="https://github.com/user-attachments/assets/879221d0-bf19-4760-adbb-aea0b646bf6c" />


---

### 4. Experiments – Combined Policies
```bash
python -m smartgrid.experiments_combined
```
- Compares classical vs combined schedulers (WRR+EDF, WRR+NPPS)  
- With and without outages  
- Plots:  
  - Avg Wait comparison  
  - Deadline Drops comparison  

<img width="900" height="500" alt="Figure_4 1" src="https://github.com/user-attachments/assets/c84a8414-2b4f-440f-8548-65b816be8341" />
<img width="900" height="500" alt="Figure_4 2" src="https://github.com/user-attachments/assets/673d5dc7-a535-46cc-bd1b-9baf66b6d667" />



