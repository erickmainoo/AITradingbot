from __future__ import annotations
from typing import Optional
import pandas as pd

class MinuteAggregator:
    """Aggregate IB 5s real-time bars into 1-minute OHLCV (UTC index)."""
    def __init__(self):
        self._cur_minute = None
        self._open = self._high = self._low = self._close = None
        self._vol = 0
        self.df = pd.DataFrame(columns=['open','high','low','close','volume'])
        self.df.index.name = 'timestamp'

    def push_5s_bar(self, bar) -> Optional[pd.Series]:
        ts = pd.Timestamp(bar.time, tz='UTC')
        minute = ts.floor('T')
        finished_bar = None

        if self._cur_minute is None:
            self._cur_minute = minute
            self._open = bar.open; self._high = bar.high
            self._low = bar.low;   self._close = bar.close
            self._vol = bar.volume
            return None

        if minute == self._cur_minute:
            self._high = max(self._high, bar.high)
            self._low  = min(self._low,  bar.low)
            self._close = bar.close
            self._vol  += bar.volume
            return None
        else:
            finished_bar = pd.Series(
                {'open': self._open, 'high': self._high, 'low': self._low,
                 'close': self._close, 'volume': self._vol},
                name=self._cur_minute
            )
            self.df.loc[self._cur_minute] = finished_bar
            # start new minute
            self._cur_minute = minute
            self._open = bar.open; self._high = bar.high
            self._low  = bar.low;  self._close = bar.close
            self._vol  = bar.volume
            return finished_bar
