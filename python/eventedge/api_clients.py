from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


@dataclass
class SnapshotResult:
    source: str
    rows: list[dict[str, Any]]
    raw_path: str | None = None


class PolymarketClient:
    """Best-effort public Polymarket client.

    Polymarket public market-discovery and data endpoints generally do not require auth,
    but response schemas may evolve. This client saves raw JSON so the project remains
    inspectable even if normalization needs adjustment.
    """

    def __init__(self, gamma_base: str = "https://gamma-api.polymarket.com"):
        self.gamma_base = gamma_base.rstrip("/")

    def fetch_markets(self, limit: int = 20, active: bool = True) -> SnapshotResult:
        params = {"limit": limit, "active": str(active).lower()}
        url = f"{self.gamma_base}/markets"
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        raw = r.json()
        rows = raw if isinstance(raw, list) else raw.get("markets", []) if isinstance(raw, dict) else []
        return SnapshotResult("polymarket_gamma", rows)


class KalshiClient:
    """Kalshi REST starting point.

    Some Kalshi endpoints/environments require credentials. This class is intentionally
    conservative and primarily documents the integration seam.
    """

    def __init__(self, base_url: str = "https://api.elections.kalshi.com/trade-api/v2"):
        self.base_url = base_url.rstrip("/")
        self.api_key = os.getenv("KALSHI_API_KEY")

    def fetch_markets(self, limit: int = 20) -> SnapshotResult:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        url = f"{self.base_url}/markets"
        r = requests.get(url, params={"limit": limit}, headers=headers, timeout=15)
        r.raise_for_status()
        raw = r.json()
        rows = raw.get("markets", []) if isinstance(raw, dict) else []
        return SnapshotResult("kalshi", rows)


class GdeltClient:
    def __init__(self, base: str = "https://api.gdeltproject.org/api/v2/doc/doc"):
        self.base = base

    def search_articles(self, query: str, mode: str = "ArtList", max_records: int = 20) -> SnapshotResult:
        params = {
            "query": query,
            "mode": mode,
            "format": "json",
            "maxrecords": max_records,
            "sort": "HybridRel",
        }
        r = requests.get(self.base, params=params, timeout=20)
        r.raise_for_status()
        raw = r.json()
        articles = raw.get("articles", []) if isinstance(raw, dict) else []
        return SnapshotResult("gdelt", articles)


def save_raw(snapshot: SnapshotResult, out_dir: str = "data/raw") -> SnapshotResult:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = Path(out_dir) / f"{snapshot.source}_{ts}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(snapshot.rows, f, indent=2, ensure_ascii=False)
    snapshot.raw_path = str(path)
    return snapshot
