#pragma once
#include <string>
#include <unordered_map>
#include <vector>

struct OrderBookRow {
    std::string ts, venue, market;
    double bid = 0, ask = 0, bid_size = 0, ask_size = 0;
    double mid() const { return 0.5 * (bid + ask); }
    double spread() const { return ask - bid; }
};

struct FairValueRow {
    std::string ts, market;
    double fair = 0, confidence = 0, news_score = 0, imbalance = 0;
};

struct SettlementRow {
    std::string market;
    int outcome = 0;
    double payout = 1.0;
};

struct Position {
    int qty = 0;
    double avg_cost = 0.0;
};

struct BacktestConfig {
    double min_edge = 0.025;
    double max_spread = 0.06;
    int max_position = 100;
    int order_size = 10;
    double fee_per_contract = 0.002;
};

struct BacktestResult {
    double cash = 0.0;
    double settlement_pnl = 0.0;
    int trades = 0;
    std::unordered_map<std::string, Position> positions;
};

BacktestResult run_backtest(
    const std::vector<OrderBookRow>& books,
    const std::unordered_map<std::string, FairValueRow>& fair_by_key,
    const std::unordered_map<std::string, SettlementRow>& settlements,
    const BacktestConfig& cfg
);
