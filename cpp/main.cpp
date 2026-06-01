#include "csv.hpp"
#include "simulator.hpp"
#include <iostream>
#include <unordered_map>

static std::string key(const std::string& ts, const std::string& market) { return ts + "|" + market; }

int main(int argc, char** argv) {
    if (argc != 4) {
        std::cerr << "usage: " << argv[0] << " data/orderbooks.csv data/fair_values.csv data/settlements.csv\n";
        return 1;
    }

    std::vector<OrderBookRow> books;
    for (auto& r : read_csv_dicts(argv[1])) {
        OrderBookRow ob;
        ob.ts = r["ts"]; ob.venue = r["venue"]; ob.market = r["market"];
        ob.bid = to_double(r["bid"]); ob.ask = to_double(r["ask"]);
        ob.bid_size = to_double(r["bid_size"]); ob.ask_size = to_double(r["ask_size"]);
        books.push_back(ob);
    }

    std::unordered_map<std::string, FairValueRow> fair;
    for (auto& r : read_csv_dicts(argv[2])) {
        FairValueRow fv;
        fv.ts = r["ts"]; fv.market = r["market"];
        fv.fair = to_double(r["fair"]); fv.confidence = to_double(r["confidence"]);
        fv.news_score = to_double(r["news_score"]); fv.imbalance = to_double(r["imbalance"]);
        fair[key(fv.ts, fv.market)] = fv;
    }

    std::unordered_map<std::string, SettlementRow> settlements;
    for (auto& r : read_csv_dicts(argv[3])) {
        SettlementRow s;
        s.market = r["market"]; s.outcome = to_int(r["outcome"]); s.payout = to_double(r["payout"], 1.0);
        settlements[s.market] = s;
    }

    BacktestConfig cfg;
    auto res = run_backtest(books, fair, settlements, cfg);

    std::cout << "EventEdge C++ backtest\n";
    std::cout << "trades=" << res.trades << "\n";
    std::cout << "cash=" << res.cash << "\n";
    std::cout << "settlement_pnl=" << res.settlement_pnl << "\n";
    std::cout << "total_pnl=" << (res.cash + res.settlement_pnl) << "\n";
    std::cout << "positions:\n";
    for (const auto& kv : res.positions) {
        std::cout << "  " << kv.first << " qty=" << kv.second.qty << "\n";
    }
    return 0;
}
