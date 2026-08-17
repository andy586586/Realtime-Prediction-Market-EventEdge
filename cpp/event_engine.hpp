#pragma once

#include "market_event.hpp"
#include "order_book.hpp"
#include "simulator.hpp"

#include <cstdint>
#include <string>
#include <unordered_map>

struct EngineStats {
    std::uint64_t events = 0;
    std::uint64_t stale_quotes = 0;
    std::uint64_t trades = 0;
    double cash = 0.0;
    double marked_value = 0.0;
    double realized_value = 0.0;
    double total_pnl() const { return cash + marked_value + realized_value; }
};

class EventEngine {
public:
    explicit EventEngine(BacktestConfig config = {});

    void on_event(const MarketEvent& event);
    EngineStats stats() const;
    int position(const std::string& market) const;
    const OrderBook& order_book() const { return order_book_; }

private:
    void evaluate(const std::string& market);

    BacktestConfig config_;
    OrderBook order_book_;
    std::unordered_map<std::string, double> fair_values_;
    std::unordered_map<std::string, int> positions_;
    EngineStats stats_;
};
