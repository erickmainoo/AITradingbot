
from dataclasses import dataclass

@dataclass
class MarketEvent:
    pass

@dataclass
class SignalEvent:
    timestamp: object
    direction: int  # -1, 0, +1

@dataclass
class OrderEvent:
    timestamp: object
    direction: int
    size: int

@dataclass
class FillEvent:
    timestamp: object
    price: float
    size: int
    commission: float
