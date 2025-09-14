
import numpy as np
import pandas as pd

def annualize_factor(freq='1min'):
    # Approx minutes in RTH per year
    return np.sqrt(252 * 6.5 * 60)

def summarize(equity_df: pd.DataFrame) -> dict:
    pnl = equity_df['pnl_after_costs']
    ret = pnl  # dollar returns; for Sharpe on $ we normalize
    # Convert to per-minute returns in dollars. Use std dev and annualize.
    af = annualize_factor()
    sharpe = (ret.mean() / (ret.std() + 1e-9)) * af
    eq = equity_df['equity']
    peak = eq.cummax()
    dd = (eq - peak)
    max_dd = dd.min()
    total_pnl = eq.iloc[-1] if len(eq) else 0.0
    trades = (equity_df['trade'].abs() > 0).sum()
    return {
        'sharpe_approx': float(sharpe),
        'max_drawdown_$': float(max_dd),
        'total_pnl_$': float(total_pnl),
        'num_trades': int(trades)
    }
