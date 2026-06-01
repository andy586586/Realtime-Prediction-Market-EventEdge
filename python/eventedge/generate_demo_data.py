from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import random

import numpy as np
import pandas as pd

random.seed(7)
np.random.seed(7)

MARKETS = [
    ("PM_HURRICANE_FL_2026", "polymarket", "Will a named hurricane make Florida landfall in 2026?", 0.31),
    ("KX_BIRDFLU_US_2026", "kalshi", "Will US bird flu reports exceed threshold by Dec 2026?", 0.42),
    ("PM_HEATWAVE_EU_2026", "polymarket", "Will Europe record a severe heatwave in July 2026?", 0.36),
]

NEWS_TEMPLATES = {
    "PM_HURRICANE_FL_2026": [
        "confirmed tropical system surge increases landfall probability",
        "storm weakens and landfall unlikely according to forecasters",
        "emergency officials discuss evacuation risk before hurricane season",
    ],
    "KX_BIRDFLU_US_2026": [
        "confirmed outbreak in migratory birds raises surveillance concerns",
        "avian flu reports contained after normal migration testing",
        "record bird migration anomaly escalates outbreak probability",
    ],
    "PM_HEATWAVE_EU_2026": [
        "record temperature outlook increases heatwave risk",
        "normal seasonal forecast makes severe heatwave unlikely",
        "emergency heat plans escalate after climate outlook update",
    ],
}


def main() -> None:
    Path("data").mkdir(exist_ok=True)
    start = datetime(2026, 6, 1, 13, 30, tzinfo=timezone.utc)

    ticks = []
    news = []
    settlements = []

    for market, venue, description, p0 in MARKETS:
        p = p0
        true_prob = p0 + np.random.normal(0, 0.02)
        for i in range(360):
            ts = start + timedelta(seconds=10 * i)
            p += np.random.normal(0, 0.003)
            p = float(np.clip(p, 0.03, 0.97))
            spread = float(np.clip(0.025 + abs(np.random.normal(0, 0.009)), 0.01, 0.08))
            bid = round(max(0.01, p - spread / 2), 4)
            ask = round(min(0.99, p + spread / 2), 4)
            ticks.append({
                "ts": ts.isoformat(), "venue": venue, "market": market,
                "description": description, "bid": bid, "ask": ask,
                "bid_size": int(np.random.randint(20, 300)),
                "ask_size": int(np.random.randint(20, 300)),
            })

            if i in {40, 90, 160, 250, 310}:
                title = random.choice(NEWS_TEMPLATES[market])
                news.append({
                    "ts": ts.isoformat(), "market": market, "source": "demo_gdelt",
                    "title": title, "url": "https://example.com/demo-news"
                })
                true_prob += 0.03 if any(w in title for w in ["confirmed", "record", "emergency", "escalates"]) else -0.025

        outcome = int(np.random.random() < np.clip(true_prob, 0.05, 0.95))
        settlements.append({"market": market, "outcome": outcome, "payout": 1.0})

    pd.DataFrame(ticks).to_csv("data/orderbooks.csv", index=False)
    pd.DataFrame(news).to_csv("data/news.csv", index=False)
    pd.DataFrame(settlements).to_csv("data/settlements.csv", index=False)
    print("wrote data/orderbooks.csv data/news.csv data/settlements.csv")


if __name__ == "__main__":
    main()
