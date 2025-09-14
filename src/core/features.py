
import pandas as pd

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = (df['high'] - df['low']).abs()
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def breakout_signal(df: pd.DataFrame, lookback: int = 20) -> pd.Series:
    hh = df['high'].rolling(lookback).max()
    ll = df['low'].rolling(lookback).min()
    long_sig = (df['close'] > hh.shift()).astype(int)
    short_sig = (df['close'] < ll.shift()).astype(int) * -1
    sig = long_sig + short_sig
    sig = sig.replace(0, pd.NA).ffill().fillna(0)
    sig = sig.infer_objects(copy=False).astype(int)  # ensures numeric dtype explicitly
    return sig
