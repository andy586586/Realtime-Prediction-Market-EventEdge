#include "event_engine.hpp"

#include <cassert>
#include <cmath>
#include <iostream>

int main() {
    BacktestConfig config;
    config.min_edge = 0.02;
    EventEngine engine(config);

    engine.on_event({100, MarketEventType::Quote, "demo", "MKT", 0.40, 0.42, 100, 80});
    engine.on_event({101, MarketEventType::FairValue, "", "MKT", 0, 0, 0, 0, 0.50, 0.8});
    assert(engine.position("MKT") == 10);
    assert(engine.stats().trades == 1);

    // The older quote must not replace the current top of book or trigger work.
    engine.on_event({99, MarketEventType::Quote, "demo", "MKT", 0.10, 0.12, 1, 1});
    assert(engine.stats().stale_quotes == 1);
    assert(std::abs(engine.order_book().find("MKT")->mid() - 0.41) < 1e-9);

    engine.on_event({102, MarketEventType::Settlement, "", "MKT", 0, 0, 0, 0, 0, 0, 1, 1.0});
    assert(engine.position("MKT") == 0);
    assert(engine.stats().realized_value == 10.0);

    std::cout << "event engine tests passed\n";
}
