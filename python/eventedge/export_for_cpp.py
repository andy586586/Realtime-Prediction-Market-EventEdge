from pathlib import Path

import pandas as pd


def main() -> None:
    required = ["data/orderbooks.csv", "data/fair_values.csv", "data/settlements.csv"]
    missing = [p for p in required if not Path(p).exists()]
    if missing:
        raise SystemExit(f"missing files: {missing}")
    # Normalize timestamp strings and sort deterministically.
    for path in required:
        df = pd.read_csv(path)
        if "ts" in df.columns:
            df = df.sort_values(["ts", "market"])
        df.to_csv(path, index=False)
    print("validated C++ input CSVs")


if __name__ == "__main__":
    main()
