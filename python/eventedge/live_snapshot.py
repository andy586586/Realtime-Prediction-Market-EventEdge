from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .api_clients import GdeltClient, KalshiClient, PolymarketClient, save_raw
from .features import news_score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="hurricane OR outbreak OR election")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--skip-kalshi", action="store_true")
    args = parser.parse_args()

    Path("data/raw").mkdir(parents=True, exist_ok=True)

    gdelt = save_raw(GdeltClient().search_articles(args.query, max_records=args.limit))
    rows = []
    for a in gdelt.rows:
        title = a.get("title", "")
        rows.append({"title": title, "url": a.get("url", ""), "score": news_score(title)})
    pd.DataFrame(rows).to_csv("data/live_gdelt_articles.csv", index=False)
    print(f"GDELT articles: {len(rows)} raw={gdelt.raw_path}")

    try:
        pm = save_raw(PolymarketClient().fetch_markets(limit=args.limit))
        print(f"Polymarket markets: {len(pm.rows)} raw={pm.raw_path}")
    except Exception as e:
        print(f"Polymarket snapshot failed: {e}")

    if not args.skip_kalshi:
        try:
            kalshi = save_raw(KalshiClient().fetch_markets(limit=args.limit))
            print(f"Kalshi markets: {len(kalshi.rows)} raw={kalshi.raw_path}")
        except Exception as e:
            print(f"Kalshi snapshot failed, usually auth/env related: {e}")


if __name__ == "__main__":
    main()
