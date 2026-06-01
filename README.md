# EventEdge Realtime

A runnable prediction-market fair-value engine designed for a Prediction Markets Trader portfolio project.

Real sources of alpha and advanced methods are hidden.

The project is a project only and not a real-time trading system that is used on any financial markets. Do not utilize someone else's code for actual purposes, you are solely responsible for any of your actions and the profit and/or loss.

It includes:

- Python live/offline collectors for Polymarket, Kalshi-style orderbooks, and GDELT news
- Bayesian fair-value updates from news intensity/sentiment
- q/kdb+ tick-store schema and analytics queries
- C++17 order book simulator/backtester with fills, inventory, fees, settlement, and PnL
- Offline demo mode that runs without API keys or kdb+


## Quick start: offline demo

```bash
cd eventedge_realtime
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m python.eventedge.generate_demo_data
python -m python.eventedge.build_fair_values --offline
python -m python.eventedge.export_for_cpp
bash scripts/build_cpp.sh
./build/eventedge_backtest data/orderbooks.csv data/fair_values.csv data/settlements.csv
```

Expected output includes final cash, inventory, settled PnL, and trade count.

## Optional: q/kdb+ analytics

If q is installed:

```bash
q q/load_csv.q
q q/analytics.q
```

The q layer loads CSVs into tables, computes spreads, bars, latest fair values, mispricing, and candidate trades.

## Optional: live-ish public data fetch

This project has conservative API clients. They are meant as integration starting points, not production execution code.

```bash
python -m python.eventedge.live_snapshot --query "hurricane OR outbreak OR election" --limit 5
```

Polymarket public endpoints can change response fields, so the live client normalizes best-effort and writes raw JSON snapshots for inspection. Kalshi authenticated/live usage may require credentials depending on endpoint and environment; offline demo remains the default.

## Project structure

```text
python/eventedge/
  api_clients.py          # Polymarket/Kalshi/GDELT clients
  bayes.py                # Bayesian update logic
  features.py             # News/orderbook feature engineering
  generate_demo_data.py   # Synthetic but realistic market/news data
  build_fair_values.py    # Produces model fair values
  export_for_cpp.py       # Creates C++ input CSVs
  live_snapshot.py        # Public API snapshot helper
cpp/
  main.cpp
  csv.hpp/csv.cpp
  simulator.hpp/simulator.cpp
q/
  load_csv.q
  analytics.q
scripts/
  build_cpp.sh
```


