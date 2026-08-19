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
- A parallel, open-source QuestDB backend with equivalent SQL analytics
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

## Runnable open-source path: QuestDB

The q implementation remains intact. QuestDB provides a parallel backend that
can be started locally with Docker and queried through SQL. Python publishes the
same quote and fair-value events using ILP/HTTP; QuestDB supplies WAL-backed,
time-partitioned storage and live/historical queries in one process.

```text
CSV or live feed -> Python ILP publisher -> QuestDB -> SQL analytics
                                             |
                                             +-> C++ engine/backtest inputs
```

Run the complete demo:

```bash
python -m python.eventedge.generate_demo_data
python -m python.eventedge.build_fair_values --offline
./scripts/run_questdb_demo.sh
```

The QuestDB web console is then available at `http://localhost:9000`. Equivalent
latest-value, ASOF-join, candidate-edge, and one-minute-bar queries are in
`questdb/analytics.sql`. Stop the database with `docker compose down`; add `-v`
only when you intentionally want to delete the persisted demo volume.

Run the publisher unit tests without Docker:

```bash
python3 -m unittest tests/test_questdb_replay.py
```

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
  questdb_replay.py       # ILP/HTTP publisher for the open-source backend
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
questdb/
  analytics.sql          # SQL equivalents of the q analytics
tests/
  test_event_engine.cpp
  test_questdb_replay.py
scripts/
  build_cpp.sh
  run_questdb_demo.sh
docker-compose.yml        # Local QuestDB service and persistent volume
```
