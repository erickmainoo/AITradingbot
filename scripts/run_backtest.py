
import os
import yaml
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate

from src.utils.io import load_minute_bars
from src.core.features import atr, breakout_signal
from src.backtest.engine import CostModel, target_position_from_signal, simulate
from src.backtest.metrics import summarize

def main(cfg_path='config/config.yaml'):
    with open(cfg_path, 'r') as f:
        cfg = yaml.safe_load(f)

    artifacts_dir = cfg.get('artifacts_dir', 'artifacts')
    os.makedirs(artifacts_dir, exist_ok=True)

    # 1) Load data (synthetic by default)
    data_cfg = (cfg.get('data') or {})
    df = load_minute_bars(
    path=data_cfg.get('path'),
    start=cfg['backtest']['start'],
    end=cfg['backtest']['end']
)
    # Optional RTH filter
    if data_cfg.get('rth_only'):
    # Work in US Central to cut regular session, then convert back to UTC
        df_local = df.tz_convert('America/Chicago')
        start_t = data_cfg.get('rth_start', '08:30')
        end_t   = data_cfg.get('rth_end',   '15:00')
        df_local = df_local.between_time(start_t, end_t)
        df = df_local.tz_convert('UTC')



    # 2) Compute features & signals
    a = atr(df, period=cfg['strategy']['atr_period'])
    sig = breakout_signal(df, lookback=cfg['strategy']['lookback'])

    # Vol proxy: rolling std of returns in points
    ret = df['close'].pct_change().fillna(0)
    vol = ret.rolling(60).std().bfill()


    # 3) Turn signal into target position with vol targeting
    pos = target_position_from_signal(sig, vol, cfg['strategy']['vol_target_annual'])

    # 4) Simulate with costs
    cm = CostModel(
        fees_per_contract=cfg['backtest']['fees_per_contract'],
        slippage_ticks=cfg['backtest']['slippage_ticks'],
        tick_value=cfg['market']['tick_value'],
        tick_size=cfg['market']['tick_size'],
    )
    equity = simulate(df, pos, cm)

    # 5) Metrics
    stats = summarize(equity)
    print(tabulate([[k, v] for k,v in stats.items()], headers=['Metric','Value'], tablefmt='github'))

    # 6) Save artifacts
    equity.to_csv(os.path.join(artifacts_dir, 'equity_curve.csv'))
    fig = plt.figure(figsize=(10,4))
    equity['equity'].plot()
    plt.title('Equity Curve (Synthetic)')
    plt.tight_layout()
    plt.savefig(os.path.join(artifacts_dir, 'equity_curve.png'))
    plt.close(fig)

    print(f"\nArtifacts saved to: {os.path.abspath(artifacts_dir)}")

if __name__ == '__main__':
    main()
