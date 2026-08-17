# Real-Time (Prediction Market) EventEdge

A runnable prediction-market fair-value engine designed for a Prediction Markets Trader portfolio project.

The real-time path uses a small TICK-style q/kdb+ topology and a typed C++ event
engine:

```text
Polymarket / Kalshi / news
            |
            v
   normalized market events
            |
            v
    q tickerplant (:5010)
       /             \
      v               v
 RDB (:5011)       append log
      |               |
live analytics        v
      |          date-partitioned HDB
      +-------+-------+
              v
      C++ event engine / backtest
```

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

Expected output includes final cash, inventory, settled PnL, and trade count. The
build script also runs a focused event-engine test covering decisions, stale quote
handling, and settlement.

## Optional: q/kdb+ analytics

If q is installed:

```bash
q q/load_csv.q
q q/analytics.q
```

The q layer loads CSVs into tables, computes spreads, bars, latest fair values, mispricing, and candidate trades.

For the multi-process real-time path, use three terminals from the repository root:

```bash
q q/tick.q -p 5010
q q/rdb.q -p 5011
q q/replay.q
```

Connect a q session to port 5011 and run `latestEdges[]` or
`candidateTrades[0.025;0.06]`. `q/eod.q` supplies the persistence boundary for a
date-partitioned historical database. The q runtime is not bundled with the repo.

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
  market_event.hpp       # Typed quote, fair-value, and settlement events
  order_book.hpp         # Timestamp-aware top-of-book state
  event_engine.hpp/.cpp  # Event decisions, positions, and marked PnL
q/
  load_csv.q
  analytics.q
  tick.q                 # Tickerplant / publisher
  rdb.q                  # Intraday subscriber and live queries
  replay.q               # CSV feed replay
  eod.q                  # HDB persistence boundary
tests/
  test_event_engine.cpp
scripts/
  build_cpp.sh
```

