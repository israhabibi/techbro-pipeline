"""Analyze generated CSVs: uv run --locked --extra analysis python dataset/sample_code.py."""

import os
from pathlib import Path

import pandas as pd


def main():
    folder = Path(os.environ.get("DATASET_DIR", Path(__file__).resolve().parent))
    tables = {
        name: pd.read_csv(folder / f"techbro_{name}.csv")
        for name in ("tweets", "activity", "topics")
    }
    for name, table in tables.items():
        print(f"{name}: {len(table)} rows")
    activity = tables["activity"]
    print("Tweets per day:")
    print(activity.groupby("day")["tweet_count"].sum().sort_index())
    print("Most active contributors:")
    print(
        activity.groupby("user_handle")["tweet_count"].sum().sort_values(ascending=False).head(10)
    )
    print("Topics:")
    print(tables["topics"][["topic", "tweet_count"]].to_string(index=False))


if __name__ == "__main__":
    main()
