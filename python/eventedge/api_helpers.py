"""
realtime_helpers.py

Purpose:
- Fetch real public market metadata/snapshots from Polymarket Gamma.
- Fetch public Polymarket CLOB order books for token IDs when available.
- Fetch public Kalshi market snapshots/order books.
- Fetch real GDELT DOC 2.0 article lists.
- Convert snapshots into EventEdge-compatible CSVs:
    data/quotes.csv
    data/signals.csv
    data/raw_news.csv

Notes:
- Public reads only. No authenticated trading in this file.
- Polymarket Gamma/Data and public CLOB read endpoints do not require auth.
- Kalshi public market-data endpoints do not require auth for browsing market data.
- GDELT is public.

Install:
    python -m pip install requests pandas

Example:
    python python/realtime_helpers.py --query "hurricane Florida" --limit 20 --out data
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests


# -----------------------------
# Generic HTTP helper
# -----------------------------

class HttpClient:
    def __init__(self, timeout: float = 15.0, retries: int = 2, backoff: float = 0.75):
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PLACEHOLDER/0.1 (+https://github.com/githubusername/placeholder)",
            "Accept": "application/json,text/plain,*/*",
        })

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        last_err: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                r = self.session.get(url, params=params, timeout=self.timeout)
                r.raise_for_status()
                if not r.text.strip():
                    return {}
                return r.json()
            except Exception as e:  # intentionally broad for retry wrapper
                last_err = e
                if attempt < self.retries:
                    time.sleep(self.backoff * (attempt + 1))
        raise RuntimeError(f"GET failed url={url} params={params}: {last_err}")


def now_ms() -> int:
    return int(time.time() * 1000)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_float(x: Any, default: float = float("nan")) -> float:
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default


def parse_jsonish_array(x: Any) -> List[Any]:
    """Polymarket often returns fields like '["Yes", "No"]' as strings."""
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        try:
            v = json.loads(x)
            return v if isinstance(v, list) else []
        except Exception:
            return []
    return []


# -----------------------------
# Unified records
# -----------------------------

@dataclass
class QuoteRow:
    ts_ms: int
    source: str
    market_id: str
    title: str
    token_id: str
    bid: float
    ask: float
    mid: float
    spread: float


@dataclass
class NewsRow:
    ts_iso: str
    query: str
    title: str
    url: str
    domain: str
    seendate: str
    source_country: str
    tone: float
    score: float


@dataclass
class SignalRow:
    ts_ms: int
    market_id: str
    title: str
    prior: float
    news_score: float
    likelihood_ratio: float
    fair: float
    confidence: float


# -----------------------------
# Polymarket public clients
# -----------------------------

class PolymarketClient:
    GAMMA = "https://gamma-api.polymarket.com"
    CLOB = "https://clob.polymarket.com"

    def __init__(self, http: Optional[HttpClient] = None):
        self.http = http or HttpClient()

    def events(self, *, limit: int = 100, active: bool = True, closed: bool = False, **extra: Any) -> List[Dict[str, Any]]:
        params = {"limit": limit, "active": str(active).lower(), "closed": str(closed).lower()}
        params.update(extra)
        data = self.http.get_json(f"{self.GAMMA}/events", params=params)
        return data if isinstance(data, list) else data.get("events", [])

    def markets(self, *, limit: int = 100, active: bool = True, closed: bool = False, **extra: Any) -> List[Dict[str, Any]]:
        params = {"limit": limit, "active": str(active).lower(), "closed": str(closed).lower()}
        params.update(extra)
        data = self.http.get_json(f"{self.GAMMA}/markets", params=params)
        return data if isinstance(data, list) else data.get("markets", [])

    def search_markets(self, query: str, *, limit: int = 100) -> List[Dict[str, Any]]:
        # Gamma does not always expose a uniform search endpoint in all mirrors,
        # so fetch active markets and filter client-side.
        q = query.lower()
        mkts = self.markets(limit=limit, active=True, closed=False)
        return [m for m in mkts if q in str(m.get("question", m.get("title", ""))).lower()]

    def book(self, token_id: str) -> Dict[str, Any]:
        # Public CLOB orderbook read. Response shape may contain bids/asks arrays.
        return self.http.get_json(f"{self.CLOB}/book", params={"token_id": token_id})

    def quote_rows_from_markets(self, markets: Iterable[Dict[str, Any]], *, fetch_books: bool = True) -> List[QuoteRow]:
        rows: List[QuoteRow] = []
        ts = now_ms()

        for m in markets:
            market_id = str(m.get("id") or m.get("conditionId") or m.get("slug") or "")
            title = str(m.get("question") or m.get("title") or m.get("slug") or market_id)

            outcomes = parse_jsonish_array(m.get("outcomes"))
            outcome_prices = parse_jsonish_array(m.get("outcomePrices"))
            token_ids = parse_jsonish_array(m.get("clobTokenIds"))

            # Prefer YES leg if present; otherwise index 0.
            idx = 0
            for i, out in enumerate(outcomes):
                if str(out).strip().lower() == "yes":
                    idx = i
                    break

            fallback_mid = safe_float(outcome_prices[idx] if idx < len(outcome_prices) else None, default=float("nan"))
            token_id = str(token_ids[idx]) if idx < len(token_ids) else ""

            bid = ask = float("nan")
            if fetch_books and token_id:
                try:
                    b = self.book(token_id)
                    bids = b.get("bids", []) or []
                    asks = b.get("asks", []) or []
                    # CLOB book entries are commonly dicts with price/size strings.
                    if bids:
                        bid = max(safe_float(x.get("price") if isinstance(x, dict) else x[0]) for x in bids)
                    if asks:
                        ask = min(safe_float(x.get("price") if isinstance(x, dict) else x[0]) for x in asks)
                except Exception:
                    pass

            if math.isnan(bid) or math.isnan(ask):
                # If book unavailable, synthesize a narrow quote around Gamma implied probability.
                # This still marks source as Polymarket but lets downstream tools run.
                mid = fallback_mid
                if math.isnan(mid):
                    continue
                bid = max(0.0, mid - 0.01)
                ask = min(1.0, mid + 0.01)
            else:
                mid = (bid + ask) / 2.0

            rows.append(QuoteRow(
                ts_ms=ts,
                source="polymarket",
                market_id=market_id,
                title=title,
                token_id=token_id,
                bid=bid,
                ask=ask,
                mid=(bid + ask) / 2.0,
                spread=max(0.0, ask - bid),
            ))
        return rows


# -----------------------------
# Kalshi public client
# -----------------------------

class KalshiClient:
    BASE = "https://api.elections.kalshi.com/trade-api/v2"

    def __init__(self, http: Optional[HttpClient] = None):
        self.http = http or HttpClient()

    def markets(self, *, limit: int = 100, cursor: Optional[str] = None, status: str = "open", **extra: Any) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": limit, "status": status}
        if cursor:
            params["cursor"] = cursor
        params.update(extra)
        return self.http.get_json(f"{self.BASE}/markets", params=params)

    def orderbook(self, ticker: str) -> Dict[str, Any]:
        return self.http.get_json(f"{self.BASE}/markets/{ticker}/orderbook")

    def quote_rows(self, *, limit: int = 100, status: str = "open") -> List[QuoteRow]:
        data = self.markets(limit=limit, status=status)
        markets = data.get("markets", []) if isinstance(data, dict) else []
        ts = now_ms()
        rows: List[QuoteRow] = []
        for m in markets:
            ticker = str(m.get("ticker") or "")
            title = str(m.get("title") or m.get("subtitle") or ticker)
            # Kalshi prices are often in cents. Prefer explicit bid/ask fields when present.
            yes_bid = safe_float(m.get("yes_bid"), default=float("nan"))
            yes_ask = safe_float(m.get("yes_ask"), default=float("nan"))
            last_price = safe_float(m.get("last_price"), default=float("nan"))

            if yes_bid > 1.0:
                yes_bid /= 100.0
            if yes_ask > 1.0:
                yes_ask /= 100.0
            if last_price > 1.0:
                last_price /= 100.0

            if math.isnan(yes_bid) or math.isnan(yes_ask):
                if math.isnan(last_price):
                    continue
                yes_bid = max(0.0, last_price - 0.01)
                yes_ask = min(1.0, last_price + 0.01)

            rows.append(QuoteRow(
                ts_ms=ts,
                source="kalshi",
                market_id=ticker,
                title=title,
                token_id=ticker,
                bid=yes_bid,
                ask=yes_ask,
                mid=(yes_bid + yes_ask) / 2.0,
                spread=max(0.0, yes_ask - yes_bid),
            ))
        return rows


# -----------------------------
# GDELT DOC 2.0 client
# -----------------------------

class GDELTClient:
    DOC = "https://api.gdeltproject.org/api/v2/doc/doc"

    def __init__(self, http: Optional[HttpClient] = None):
        self.http = http or HttpClient(timeout=20.0)

    def articles(self, query: str, *, max_records: int = 75, timespan: str = "1d") -> List[Dict[str, Any]]:
        params = {
            "query": query,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": max_records,
            "timespan": timespan,
            "sort": "DateDesc",
        }
        data = self.http.get_json(self.DOC, params=params)
        if isinstance(data, dict):
            return data.get("articles", []) or []
        return []

    def news_rows(self, query: str, *, max_records: int = 75, timespan: str = "1d") -> List[NewsRow]:
        rows: List[NewsRow] = []
        for a in self.articles(query, max_records=max_records, timespan=timespan):
            title = str(a.get("title") or "")
            domain = str(a.get("domain") or "")
            url = str(a.get("url") or "")
            seendate = str(a.get("seendate") or a.get("seenDate") or "")
            source_country = str(a.get("sourcecountry") or a.get("sourceCountry") or "")
            tone = safe_float(a.get("tone"), default=0.0)
            score = simple_news_score(title, tone=tone)
            rows.append(NewsRow(
                ts_iso=iso_now(), query=query, title=title, url=url, domain=domain,
                seendate=seendate, source_country=source_country, tone=tone, score=score,
            ))
        return rows


# -----------------------------
# Bayesian fair-value helpers
# -----------------------------

POS_WORDS = {
    "confirmed": 0.9,
    "warning": 0.5,
    "emergency": 0.9,
    "outbreak": 1.0,
    "surge": 0.6,
    "record": 0.4,
    "landfall": 0.8,
    "evacuation": 0.7,
    "heatwave": 0.8,
    "avian flu": 1.0,
    "h5n1": 1.0,
}
NEG_WORDS = {
    "false alarm": -1.0,
    "contained": -0.8,
    "downgraded": -0.7,
    "unlikely": -0.7,
    "denies": -0.5,
    "no evidence": -0.9,
    "weakens": -0.6,
}


def simple_news_score(text: str, *, tone: float = 0.0) -> float:
    t = text.lower()
    score = 0.0
    for k, v in POS_WORDS.items():
        if k in t:
            score += v
    for k, v in NEG_WORDS.items():
        if k in t:
            score += v
    # GDELT tone can be positive/negative sentiment, but event risk can go either way.
    # Keep it weak so keywords dominate.
    score += max(-0.5, min(0.5, -tone / 20.0))
    return score


def likelihood_ratio_from_score(score: float) -> float:
    # Convert unbounded-ish news score into a moderate likelihood ratio.
    # score=0 => LR=1. score=2 => LR≈1.82. score=-2 => LR≈0.55.
    return math.exp(max(-2.0, min(2.0, score)) * 0.30)


def bayesian_update(prior: float, likelihood_ratio: float) -> float:
    prior = min(0.999, max(0.001, prior))
    odds = prior / (1.0 - prior)
    post_odds = odds * likelihood_ratio
    return post_odds / (1.0 + post_odds)


def build_signals_from_quotes_and_news(quotes: List[QuoteRow], news: List[NewsRow]) -> List[SignalRow]:
    # Simple v1: use average news score globally. Later improve by matching each market title to relevant news.
    avg_score = sum(n.score for n in news) / len(news) if news else 0.0
    lr = likelihood_ratio_from_score(avg_score)
    confidence = min(1.0, len(news) / 50.0)
    out: List[SignalRow] = []
    ts = now_ms()
    for q in quotes:
        prior = q.mid
        fair = bayesian_update(prior, lr)
        out.append(SignalRow(
            ts_ms=ts,
            market_id=q.market_id,
            title=q.title,
            prior=prior,
            news_score=avg_score,
            likelihood_ratio=lr,
            fair=fair,
            confidence=confidence,
        ))
    return out


# -----------------------------
# CSV writers for EventEdge
# -----------------------------

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def write_dataclass_csv(path: str, rows: Iterable[Any]) -> None:
    rows = list(rows)
    if not rows:
        raise ValueError(f"No rows to write: {path}")
    ensure_dir(os.path.dirname(path) or ".")
    fieldnames = list(asdict(rows[0]).keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(asdict(r))


def write_eventedge_quotes(path: str, rows: Iterable[QuoteRow]) -> None:
    """Write compact schema expected by the C++ backtester: ts_ms,market,bid,ask."""
    rows = list(rows)
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ts_ms", "market", "bid", "ask"])
        w.writeheader()
        for r in rows:
            w.writerow({"ts_ms": r.ts_ms, "market": r.market_id, "bid": r.bid, "ask": r.ask})


def write_eventedge_signals(path: str, rows: Iterable[SignalRow]) -> None:
    """Write compact schema expected by the C++ backtester: ts_ms,market,fair,confidence."""
    rows = list(rows)
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ts_ms", "market", "fair", "confidence"])
        w.writeheader()
        for r in rows:
            w.writerow({"ts_ms": r.ts_ms, "market": r.market_id, "fair": r.fair, "confidence": r.confidence})


def write_dummy_settlements(path: str, quotes: Iterable[QuoteRow]) -> None:
    """For research replay only. Real settlements should be pulled from platform resolution data."""
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["market", "payout"])
        w.writeheader()
        for q in quotes:
            # Demo placeholder: mark contracts above 50% as winners.
            w.writerow({"market": q.market_id, "payout": 1.0 if q.mid > 0.50 else 0.0})


# -----------------------------
# One-shot realtime snapshot runner
# -----------------------------

def run_snapshot(query: str, out_dir: str, limit: int, include_kalshi: bool, include_polymarket: bool) -> None:
    http = HttpClient()
    quotes: List[QuoteRow] = []

    if include_polymarket:
        pm = PolymarketClient(http)
        markets = pm.search_markets(query, limit=limit)
        if not markets:
            markets = pm.markets(limit=limit, active=True, closed=False)
        quotes.extend(pm.quote_rows_from_markets(markets[:limit], fetch_books=True))

    if include_kalshi:
        ks = KalshiClient(http)
        # Public list; filtering client-side because available filters differ by endpoint.
        krows = ks.quote_rows(limit=limit, status="open")
        qlow = query.lower()
        filtered = [r for r in krows if qlow in r.title.lower() or qlow in r.market_id.lower()]
        quotes.extend(filtered if filtered else krows[: min(limit, len(krows))])

    gdelt = GDELTClient(http)
    news = gdelt.news_rows(query, max_records=75, timespan="1d")
    signals = build_signals_from_quotes_and_news(quotes, news)

    if not quotes:
        raise RuntimeError("No market quotes fetched. Try a broader --query or check network/API availability.")

    ensure_dir(out_dir)
    write_dataclass_csv(os.path.join(out_dir, "raw_quotes_detailed.csv"), quotes)
    if news:
        write_dataclass_csv(os.path.join(out_dir, "raw_news.csv"), news)
    write_dataclass_csv(os.path.join(out_dir, "signals_detailed.csv"), signals)
    write_eventedge_quotes(os.path.join(out_dir, "quotes.csv"), quotes)
    write_eventedge_signals(os.path.join(out_dir, "signals.csv"), signals)
    write_dummy_settlements(os.path.join(out_dir, "settlements.csv"), quotes)
    write_q_orderbooks(os.path.join(out_dir, "orderbooks.csv"), quotes)
    write_q_fair_values(os.path.join(out_dir, "fair_values.csv"), signals)

    print(f"wrote {len(quotes)} quote rows to {out_dir}/quotes.csv")
    print(f"wrote {len(news)} news rows to {out_dir}/raw_news.csv")
    print(f"wrote {len(signals)} signal rows to {out_dir}/signals.csv")
    print("next:")
    print(f"  ./build/eventedge_backtest {out_dir}/quotes.csv {out_dir}/signals.csv {out_dir}/settlements.csv")


def write_q_orderbooks(path: str, rows):
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "ts", "venue", "market", "token_id",
                "bid", "ask", "bid_size", "ask_size"
            ],
        )
        w.writeheader()
        for r in rows:
            w.writerow({
                "ts": datetime.fromtimestamp(r.ts_ms / 1000, timezone.utc).isoformat(),
                "venue": r.source,
                "market": r.market_id,
                "token_id": r.token_id,
                "bid": r.bid,
                "ask": r.ask,
                "bid_size": 0.0,
                "ask_size": 0.0,
            })


def write_q_fair_values(path: str, rows):
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "ts", "market", "fair", "confidence",
                "prior", "news_score", "likelihood_ratio"
            ],
        )
        w.writeheader()
        for r in rows:
            w.writerow({
                "ts": datetime.fromtimestamp(r.ts_ms / 1000, timezone.utc).isoformat(),
                "market": r.market_id,
                "fair": r.fair,
                "confidence": r.confidence,
                "prior": r.prior,
                "news_score": r.news_score,
                "likelihood_ratio": r.likelihood_ratio,
            })

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="hurricane Florida", help="Search/news query, e.g. 'hurricane Florida' or 'avian flu US'")
    ap.add_argument("--out", default="data", help="Output directory")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--no-kalshi", action="store_true")
    ap.add_argument("--no-polymarket", action="store_true")
    args = ap.parse_args()

    run_snapshot(
        query=args.query,
        out_dir=args.out,
        limit=args.limit,
        include_kalshi=not args.no_kalshi,
        include_polymarket=not args.no_polymarket,
    )


if __name__ == "__main__":
    main()
