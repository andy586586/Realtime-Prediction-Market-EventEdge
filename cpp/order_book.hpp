#pragma once

#include "market_event.hpp"

#include <stdexcept>
#include <string>
#include <unordered_map>

struct TopOfBook {
    std::int64_t timestamp_ns = 0;
    double bid = 0.0;
    double ask = 0.0;
    double bid_size = 0.0;
    double ask_size = 0.0;

    bool valid() const { return bid > 0.0 && ask >= bid; }
    double mid() const { return 0.5 * (bid + ask); }
    double spread() const { return ask - bid; }
    double imbalance() const {
        const double total = bid_size + ask_size;
        return total > 0.0 ? (bid_size - ask_size) / total : 0.0;
    }
};

class OrderBook {
public:
    // Returns false for a stale quote. The live engine never lets an older
    // network update overwrite newer state for the same market.
    bool apply(const MarketEvent& event) {
        if (event.type != MarketEventType::Quote) {
            throw std::invalid_argument("OrderBook only accepts quote events");
        }
        auto& top = books_[event.market];
        if (top.timestamp_ns > event.timestamp_ns) return false;
        top = {event.timestamp_ns, event.bid, event.ask,
               event.bid_size, event.ask_size};
        return true;
    }

    const TopOfBook* find(const std::string& market) const {
        const auto it = books_.find(market);
        return it == books_.end() ? nullptr : &it->second;
    }

private:
    std::unordered_map<std::string, TopOfBook> books_;
};
