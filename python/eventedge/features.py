from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

POSITIVE_TERMS = {
    "confirmed": 1.2,
    "surge": 1.0,
    "outbreak": 1.5,
    "landfall": 1.3,
    "emergency": 1.1,
    "evacuation": 1.0,
    "record": 0.8,
    "escalates": 1.0,
    "probable": 0.7,
}

NEGATIVE_TERMS = {
    "contained": -1.2,
    "weakens": -1.0,
    "dismissed": -0.8,
    "denied": -0.9,
    "unlikely": -1.0,
    "normal": -0.5,
    "cancelled": -0.7,
}

@dataclass
class NewsArticle:
    ts: str
    title: str
    source: str = "gdelt"
    url: str = ""


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]+", text.lower())


def news_score(text: str) -> float:
    toks = tokenize(text)
    score = 0.0
    for t in toks:
        score += POSITIVE_TERMS.get(t, 0.0)
        score += NEGATIVE_TERMS.get(t, 0.0)
    return score


def aggregate_news_score(articles: Iterable[NewsArticle]) -> float:
    scores = [news_score(a.title) for a in articles]
    if not scores:
        return 0.0
    # damp extreme article-count effects while preserving sign
    raw = sum(scores)
    return raw / (1.0 + 0.2 * max(0, len(scores) - 1))


def orderbook_imbalance(best_bid_size: float, best_ask_size: float) -> float:
    denom = best_bid_size + best_ask_size
    if denom <= 0:
        return 0.0
    return (best_bid_size - best_ask_size) / denom
