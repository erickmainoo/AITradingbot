
# AI Futures Bot — Starter

An event-driven, research-first scaffold for building and **paper-trading** an AI futures bot (start with CME Micro E-mini S&P, symbol `MES`). This repo gives you a clean, resume-ready starting point that **runs end-to-end on synthetic data** so you can plug in real market data later.

## Quickstart

### Option A: Local Python
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python scripts/run_backtest.py
```

### Option B: Docker
```bash
docker build -t ai-futures-bot .
docker run --rm -it -v $PWD:/app ai-futures-bot python scripts/run_backtest.py
```

This runs a **breakout-with-ATR** baseline on synthetic price data and prints metrics + saves artifacts under `artifacts/`.

## Next Steps
- Replace synthetic prices with real minute bars in `src/utils/io.py` (see TODO).
- Add features & ML models under `src/core/features.py` and `src/core/models.py` (stubs included).
- Integrate paper trading via IBKR (`ib_insync`) adapter later in `src/core/broker_ib.py` (stub).

> ⚠️ Educational only — not financial advice. Trade on paper until you fully validate and understand risks.
