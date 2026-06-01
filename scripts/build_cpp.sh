#!/usr/bin/env bash
set -euo pipefail
mkdir -p build
g++ -std=c++17 -O2 -Wall -Wextra cpp/main.cpp cpp/csv.cpp cpp/simulator.cpp -o build/eventedge_backtest
