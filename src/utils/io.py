import os
import pandas as pd
import numpy as np

REQ_COLS = ['open','high','low','close','volume']

def _ensure_schema(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQ_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Data missing required columns: {missing}. "
                         f"Found: {list(df.columns)}")
    # Order + type hygiene
    df = df[REQ_COLS].copy()
    for c in REQ_COLS:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def load_minute_bars(path: str | None = None, start=None, end=None) -> pd.DataFrame:
    """
    Load 1-minute bars as a tz-aware (UTC) index DataFrame with columns:
    ['open','high','low','close','volume'].
    If `path` is None or missing, returns synthetic data (so the pipeline runs).
    """
    if path is None or not os.path.exists(path):
        # --- synthetic series for demo ---
        idx = pd.date_range(start or '2022-01-03', end or '2022-12-30', freq='1min', tz='UTC')
        idx = idx[idx.indexer_between_time('14:30', '21:00')]  # ~08:30–15:00 CT
        n = len(idx)
        np.random.seed(42)
        mu, sigma = 0.00002, 0.0007
        rets = np.random.normal(mu, sigma, n)
        price = 4800 * (1 + pd.Series(rets, index=idx)).cumprod()
        high = price * (1 + np.random.rand(n)*0.0005)
        low  = price * (1 - np.random.rand(n)*0.0005)
        open_ = price.shift(1).fillna(price.iloc[0])
        close = price
        vol = np.random.randint(1, 50, n)
        df = pd.DataFrame({'open': open_, 'high': high, 'low': low, 'close': close, 'volume': vol}, index=idx)
        df.index.name = 'timestamp'
        return df

    # --- real file path ---
    if path.endswith('.parquet'):
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path, parse_dates=['timestamp'])
        if 'timestamp' not in df.columns:
            raise ValueError("CSV must include a 'timestamp' column.")
        df = df.set_index('timestamp')

    # timezone: localize or convert to UTC
    if df.index.tz is None:
        # assume UTC if naive; change here if your file is local time
        df = df.tz_localize('UTC')
    else:
        df = df.tz_convert('UTC')

    df = df.sort_index()
    df = df[~df.index.duplicated(keep='first')]

    # schema & numeric coercion
    df = _ensure_schema(df)

    # optional date range trimming (works with tz-aware)
    if start is not None:
        df = df[df.index >= pd.Timestamp(start, tz='UTC')]
    if end is not None:
        df = df[df.index <= pd.Timestamp(end, tz='UTC')]

    return df
