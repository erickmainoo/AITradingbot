
import math
import pandas as pd
from dataclasses import dataclass

@dataclass
class CostModel:
    fees_per_contract: float = 1.20
    slippage_ticks: int = 1
    tick_value: float = 1.25
    tick_size: float = 0.25

    def cost(self, trades: pd.Series) -> pd.Series:
        # cost per trade = fees + slippage (ticks * tick_value) * |delta_position|
        trade_turnover = trades.abs()  # contracts changed
        slippage_dollars = self.slippage_ticks * self.tick_value * trade_turnover
        fees = self.fees_per_contract * trade_turnover
        return slippage_dollars + fees

def target_position_from_signal(sig: pd.Series, vol: pd.Series, vol_target_annual: float = 0.10) -> pd.Series:
    # Simple volatility targeting in contract units: pos = k / vol
    # Convert annual vol to per-bar vol target factor
    bars_per_year = 252 * 6.5 * 60  # ~ minute bars in RTH
    ann_to_bar = math.sqrt(1 / bars_per_year)
    target_bar_vol = vol_target_annual * ann_to_bar
    k = 1.0  # scale factor; tune later
    pos = k * sig * (target_bar_vol / (vol.replace(0, pd.NA))).clip(-10, 10)
    pos = pos.fillna(0)
    # Round to nearest contract (integer)
    return pos.round().astype(int)

def simulate(df: pd.DataFrame, pos: pd.Series, cost_model: CostModel) -> pd.DataFrame:
    # PnL: position * returns * point_value (approx via close-to-close differences)
    px = df['close']
    ret_points = px.diff().fillna(0) / cost_model.tick_size  # in ticks
    pnl_ticks = (pos.shift().fillna(0)) * ret_points
    pnl_dollars = pnl_ticks * cost_model.tick_value

    # Trading costs when position changes
    trades = pos.diff().fillna(pos)
    costs = cost_model.cost(trades)

    pnl_after_costs = pnl_dollars - costs
    eq = pnl_after_costs.cumsum()

    out = pd.DataFrame({
        'close': px,
        'position': pos,
        'trade': trades,
        'pnl_dollars': pnl_dollars,
        'costs': costs,
        'pnl_after_costs': pnl_after_costs,
        'equity': eq
    }, index=df.index)
    return out
