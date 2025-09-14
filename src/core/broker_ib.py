from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timezone

from ib_insync import IB, Future, MarketOrder, Contract, ContractDetails

@dataclass
class IBConfig:
    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 123

class IBPaperBroker:
    def __init__(self, cfg: IBConfig):
        self.cfg = cfg
        self.ib = IB()
        self.contract: Optional[Contract] = None
        self.current_position: int = 0

    async def connect(self):
        await self.ib.connectAsync(self.cfg.host, self.cfg.port, clientId=self.cfg.client_id)
        self.ib.errorEvent += lambda reqId, code, msg, *_: print(f"[IB ERROR] {code}: {msg}")

    async def disconnect(self):
        if self.ib.isConnected():
            await self.ib.disconnectAsync()

    async def resolve_front_future(self, symbol: str, exchange: str) -> Contract:
        """Pick the nearest non-expired MNQ contract (front month)."""
        cds: List[ContractDetails] = await self.ib.reqContractDetailsAsync(
            Future(symbol=symbol, exchange=exchange)
        )
        if not cds:
            raise RuntimeError(f"No futures found for {symbol} on {exchange}")
        now = datetime.now(timezone.utc)
        # choose first contract whose expiry >= now, else earliest
        def exp_ts(cd: ContractDetails):
            # IB format: YYYYMM or YYYYMMDD
            s = cd.contract.lastTradeDateOrContractMonth
            year = int(s[0:4]); month = int(s[4:6]); day = int(s[6:8]) if len(s) >= 8 else 28
            return datetime(year, month, day, tzinfo=timezone.utc)
        cds_sorted = sorted(cds, key=exp_ts)
        future = next((cd for cd in cds_sorted if exp_ts(cd) >= now), cds_sorted[0]).contract
        self.contract = future
        print(f"[IB] Using contract {future.localSymbol} (exp {future.lastTradeDateOrContractMonth})")
        return future

    async def get_net_position(self) -> int:
        pos_list = await self.ib.reqPositionsAsync()
        net = 0
        for acc, con, qty, avgCost in pos_list:
            if self.contract and con.conId == self.contract.conId:
                net += qty
        self.current_position = int(net)
        return self.current_position

    async def adjust_to_target(self, target: int, max_contracts: int = 1):
        target = max(-max_contracts, min(max_contracts, int(target)))
        await self.get_net_position()
        delta = target - self.current_position
        if delta == 0:
            return None
        action = "BUY" if delta > 0 else "SELL"
        qty = abs(delta)
        order = MarketOrder(action, qty)
        trade = self.ib.placeOrder(self.contract, order)
        print(f"[ORDER] {action} {qty} {self.contract.localSymbol} → target {target} (was {self.current_position})")
        while not trade.isDone():
            await asyncio.sleep(0.1)
        await self.get_net_position()
        print(f"[FILL] {trade.orderStatus.status}; new_pos={self.current_position}")
        return trade
