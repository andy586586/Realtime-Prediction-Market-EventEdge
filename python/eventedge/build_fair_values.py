from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .bayes import bayesian_logit_update, blend_market_and_model
from .features import NewsArticle, aggregate_news_score, orderbook_imbalance


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Use local data/news.csv")
    parser.add_argument("--news-window", type=int, default=900, help="Trailing news window in seconds")
    args = parser.parse_args()

    Path("data").mkdir(exist_ok=True)
    ob = pd.read_csv("data/orderbooks.csv", parse_dates=["ts"])
    news = pd.read_csv("data/news.csv", parse_dates=["ts"]) if Path("data/news.csv").exists() else pd.DataFrame(columns=["ts", "market", "title", "source", "url"])

    rows = []
    for _, row in ob.iterrows():
        market = row["market"]
        mid = (row["bid"] + row["ask"]) / 2.0
        start = row["ts"] - pd.Timedelta(seconds=args.news_window)
        recent = news[(news["market"] == market) & (news["ts"] <= row["ts"]) & (news["ts"] >= start)]
        articles = [NewsArticle(ts=str(r.ts), title=str(r.title), source=str(r.source), url=str(r.url)) for r in recent.itertuples()]
        nscore = aggregate_news_score(articles)
        imb = orderbook_imbalance(float(row["bid_size"]), float(row["ask_size"]))
        posterior = bayesian_logit_update(mid, evidence_score=nscore + 0.35 * imb, strength=0.18)
        confidence = min(1.0, 0.15 + 0.1 * len(articles) + abs(imb) * 0.25)
        fair = blend_market_and_model(mid, posterior, weight_news=confidence)
        rows.append({
            "ts": row["ts"].isoformat(), "market": market, "mid": round(mid, 5),
            "news_score": round(nscore, 5), "imbalance": round(imb, 5),
            "posterior": round(posterior, 5), "fair": round(fair, 5),
            "confidence": round(confidence, 5),
        })

    pd.DataFrame(rows).to_csv("data/fair_values.csv", index=False)
    print("wrote data/fair_values.csv")


if __name__ == "__main__":
    main()
