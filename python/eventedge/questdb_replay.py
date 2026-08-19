from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

def _tag(value: str) -> str:
    """Escape an ILP tag value without changing the market identifier."""
    return str(value).replace("\\", "\\\\").replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")


def timestamp_ns(value: str) -> int:
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1_000_000_000)


def quote_line(row: dict[str, str]) -> str:
    return (
        f"quotes,venue={_tag(row['venue'])},market={_tag(row['market'])} "
        f"bid={float(row['bid'])},ask={float(row['ask'])},"
        f"bid_size={float(row['bid_size'])},ask_size={float(row['ask_size'])} "
        f"{timestamp_ns(row['ts'])}"
    )


def fair_value_line(row: dict[str, str]) -> str:
    return (
        f"fair_values,market={_tag(row['market'])} "
        f"fair={float(row['fair'])},confidence={float(row['confidence'])},"
        f"news_score={float(row['news_score'])},imbalance={float(row['imbalance'])} "
        f"{timestamp_ns(row['ts'])}"
    )


def csv_lines(path: Path, converter) -> Iterable[str]:
    with path.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            yield converter(row)


def publish(lines: Iterable[str], base_url: str, batch_size: int = 1000) -> int:
    import requests

    endpoint = f"{base_url.rstrip('/')}/write?precision=n"
    batch: list[str] = []
    published = 0
    for line in lines:
        batch.append(line)
        if len(batch) >= batch_size:
            response = requests.post(endpoint, data="\n".join(batch), timeout=30)
            response.raise_for_status()
            published += len(batch)
            batch.clear()
    if batch:
        response = requests.post(endpoint, data="\n".join(batch), timeout=30)
        response.raise_for_status()
        published += len(batch)
    return published


def query(sql: str, base_url: str) -> dict:
    import requests

    response = requests.get(
        f"{base_url.rstrip('/')}/exec", params={"query": sql}, timeout=30
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay EventEdge CSVs into QuestDB")
    parser.add_argument("--url", default="http://localhost:9000")
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument(
        "--reset", action="store_true", help="Drop only the demo quote tables first"
    )
    args = parser.parse_args()

    if args.reset:
        query("drop table if exists quotes", args.url)
        query("drop table if exists fair_values", args.url)

    quote_count = publish(
        csv_lines(args.data / "orderbooks.csv", quote_line), args.url, args.batch_size
    )
    fair_count = publish(
        csv_lines(args.data / "fair_values.csv", fair_value_line),
        args.url,
        args.batch_size,
    )
    counts = query(
        "select 'quotes' table_name, count() rows from quotes "
        "union all select 'fair_values', count() from fair_values",
        args.url,
    )
    print(f"published quotes={quote_count} fair_values={fair_count}")
    print(counts)


if __name__ == "__main__":
    main()
