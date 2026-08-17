#pragma once

#include <cstdint>
#include <string>

enum class MarketEventType { Quote, FairValue, Settlement };

struct MarketEvent {
    std::int64_t timestamp_ns = 0;
    MarketEventType type = MarketEventType::Quote;
    std::string venue;
    std::string market;
    double bid = 0.0;
    double ask = 0.0;
    double bid_size = 0.0;
    double ask_size = 0.0;
    double fair = 0.0;
    double confidence = 0.0;
    int outcome = 0;
    double payout = 1.0;
};
