#include "simulator.hpp"
#include <algorithm>
#include <cmath>
#include <iostream>

static std::string key(const std::string& ts, const std::string& market) {
    return ts + "|" + market;
}

BacktestResult run_backtest(
    const std::vector<OrderBookRow>& books,
    const std::unordered_map<std::string, FairValueRow>& fair_by_key,
    const std::unordered_map<std::string, SettlementRow>& settlements,
    const BacktestConfig& cfg
) {
    BacktestResult res;
    for (const auto& ob : books) {
        auto it = fair_by_key.find(key(ob.ts, ob.market));
        if (it == fair_by_key.end()) continue;
        const auto& fv = it->second;
        if (ob.spread() > cfg.max_spread || ob.ask <= 0 || ob.bid <= 0) continue;

        auto& pos = res.positions[ob.market];
        double edge = fv.fair - ob.mid();
        int desired = 0;
        double price = 0.0;

        if (edge > cfg.min_edge && pos.qty < cfg.max_position) {
            desired = std::min(cfg.order_size, cfg.max_position - pos.qty);
            price = ob.ask;
        } else if (edge < -cfg.min_edge && pos.qty > -cfg.max_position) {
            desired = -std::min(cfg.order_size, cfg.max_position + pos.qty);
            price = ob.bid;
        }

        if (desired == 0) continue;
        int fill = desired;
        double fee = std::abs(fill) * cfg.fee_per_contract;
        res.cash -= fill * price; // buy positive -> spend cash; sell negative -> receive cash
        res.cash -= fee;
        pos.qty += fill;
        res.trades++;
    }

    for (const auto& kv : res.positions) {
        const auto& market = kv.first;
        const auto& pos = kv.second;
        auto sit = settlements.find(market);
        if (sit == settlements.end()) continue;
        // YES contract: long pays outcome*payout. Short owes same.
        res.settlement_pnl += pos.qty * sit->second.outcome * sit->second.payout;
    }
    return res;
}
