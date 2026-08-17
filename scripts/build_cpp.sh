#!/usr/bin/env bash
set -euo pipefail
mkdir -p build
g++ -std=c++17 -O2 -Wall -Wextra cpp/main.cpp cpp/csv.cpp cpp/simulator.cpp -o build/eventedge_backtest
g++ -std=c++17 -O2 -Wall -Wextra -Icpp tests/test_event_engine.cpp cpp/event_engine.cpp -o build/test_event_engine
./build/test_event_engine
