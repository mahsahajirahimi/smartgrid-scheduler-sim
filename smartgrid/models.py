from dataclasses import dataclass
from typing import Optional

@dataclass
class Request:
    req_id: int
    consumer_id: int
    arrival_time: float
    demand: float  # abstract units
    priority: int  # 1..3 for NPPS
    deadline: float  # absolute time for EDF
    group: str = "A"  # for WRR later
    chosen_source: Optional[str] = None
    start_service_time: Optional[float] = None
    finish_time: Optional[float] = None

@dataclass
class Consumer:
    consumer_id: int
    demand_mean: float = 1.0

@dataclass
class EnergySource:
    name: str
    kind: str  # 'renewable', 'nonrenewable', 'battery'
