import asyncio, argparse, yaml, pandas as pd
from ib_insync import util
from src.core.broker_ib import IBPaperBroker, IBConfig
from src.core.features import breakout_signal
from src.utils.minute_agg import MinuteAggregator

def in_rth(now_utc: pd.Timestamp, tz: str, start: str, end: str) -> bool:
    local = now_utc.tz_convert(tz)
    return (local.time() >= pd.to_datetime(start).time()
            and local.time() <= pd.to_datetime(end).time())

async def run():
    # 1) Load config
    with open('config/ib.yaml', 'r') as f:
        cfg = yaml.safe_load(f)
    ib_cfg = IBConfig(**cfg['ib'])
    market = cfg['market']; strat = cfg['strategy']; risk = cfg['risk']

    # 2) Connect & resolve MNQ front month
    broker = IBPaperBroker(ib_cfg)
    await broker.connect()
    contract = await broker.resolve_front_future(symbol=market['symbol'], exchange=market['exchange'])

    # 3) Seed with 1-2 days of 1-minute history (gives the signal initial context)
    hist = await broker.ib.reqHistoricalDataAsync(
        contract, endDateTime='', durationStr='2 D', barSizeSetting='1 min',
        whatToShow='TRADES', useRTH=False, formatDate=1, keepUpToDate=False
    )
    df_hist = util.df(hist)
    if not df_hist.empty:
        df_hist['timestamp'] = pd.to_datetime(df_hist['date'], utc=True)
        df_hist = df_hist.set_index('timestamp')[['open','high','low','close','volume']].sort_index()
    else:
        df_hist = pd.DataFrame(columns=['open','high','low','close','volume'],
                               index=pd.DatetimeIndex([], tz='UTC'))
    print(f"[IB] Seed history bars: {len(df_hist)}")

    # 4) Subscribe to 5-second real-time bars and aggregate to 1 minute
    bars = broker.ib.reqRealTimeBars(contract, 5, 'TRADES', True)
    agg = MinuteAggregator()
    if not df_hist.empty:
        agg.df = df_hist.copy()

    q = asyncio.Queue()  # finished-minute queue
    lookback = int(strat.get('lookback', 20))
    tz = market.get('timezone', 'America/Chicago')
    rth_only = bool(market.get('rth_only', True))
    rth_start = market.get('rth_start', '08:30')
    rth_end   = market.get('rth_end',   '15:00')
    max_contracts = int(risk.get('max_contracts', 1))
    flatten_at_end = bool(risk.get('flatten_at_end', True))

    def on_rtb(bars, hasNewBar):
        bar = bars[-1]
        finished = agg.push_5s_bar(bar)
        if finished is not None:
            try:
                q.put_nowait(finished)
            except Exception:
                pass
    bars.updateEvent += on_rtb

    print("[LIVE] Running… Ctrl+C to exit")
    try:
        while True:
            finished_bar = await q.get()  # wait for a completed minute
            now_utc = pd.Timestamp.utcnow().tz_localize('UTC')

            # Optional: RTH enforcement and end-of-day flatten
            if rth_only and not in_rth(now_utc, tz, rth_start, rth_end):
                if flatten_at_end:
                    await broker.adjust_to_target(0, max_contracts=max_contracts)
                else:
                    print("[RTH] Out of session; standing by")
                continue

            df = agg.df.copy()
            if len(df) < lookback + 5:
                print(f"[LIVE] Need more history: {len(df)} bars")
                continue

            sig = breakout_signal(df, lookback=lookback)  # returns -1/0/+1 sticky signal
            target = int(sig.iloc[-1])
            print(f"[SIGNAL] {df.index[-1]} sig={target} close={df['close'].iloc[-1]:.2f}")
            await broker.adjust_to_target(target, max_contracts=max_contracts)
    except KeyboardInterrupt:
        print("\n[EXIT] Flattening and disconnecting…")
        try:
            await broker.adjust_to_target(0, max_contracts=max_contracts)
        except Exception as e:
            print(f"[WARN] Flatten failed: {e}")
    finally:
        await broker.disconnect()
        print("[IB] Disconnected")

if __name__ == "__main__":
    asyncio.run(run())
