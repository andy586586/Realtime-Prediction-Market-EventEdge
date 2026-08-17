#include "event_engine.hpp"

#include <algorithm>
#include <cmath>

EventEngine::EventEngine(BacktestConfig config) : config_(config) {}

void EventEngine::on_event(const MarketEvent& event) {
    ++stats_.events;
    if (event.type == MarketEventType::Quote) {
        if (!order_book_.apply(event)) {
            ++stats_.stale_quotes;
            return;
        }
        evaluate(event.market);
    } else if (event.type == MarketEventType::FairValue) {
        fair_values_[event.market] = event.fair;
        evaluate(event.market);
    } else {
        const int qty = position(event.market);
        stats_.realized_value += qty * event.outcome * event.payout;
        positions_[event.market] = 0;
    }
}

void EventEngine::evaluate(const std::string& market) {
    const auto* book = order_book_.find(market);
    const auto fair = fair_values_.find(market);
    if (!book || !book->valid() || fair == fair_values_.end() ||
        book->spread() > config_.max_spread) return;

    int& qty = positions_[market];
    int fill = 0;
    double price = 0.0;
    const double edge = fair->second - book->mid();
    if (edge > config_.min_edge && qty < config_.max_position) {
        fill = std::min(config_.order_size, config_.max_position - qty);
        price = book->ask;
    } else if (edge < -config_.min_edge && qty > -config_.max_position) {
        fill = -std::min(config_.order_size, config_.max_position + qty);
        price = book->bid;
    }
    if (!fill) return;

    stats_.cash -= fill * price;
    stats_.cash -= std::abs(fill) * config_.fee_per_contract;
    qty += fill;
    ++stats_.trades;
}

EngineStats EventEngine::stats() const {
    EngineStats snapshot = stats_;
    snapshot.marked_value = 0.0;
    for (const auto& [market, qty] : positions_) {
        if (const auto* book = order_book_.find(market); book && book->valid()) {
            snapshot.marked_value += qty * book->mid();
        }
    }
    return snapshot;
}

int EventEngine::position(const std::string& market) const {
    const auto it = positions_.find(market);
    return it == positions_.end() ? 0 : it->second;
}
