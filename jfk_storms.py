"""
JetBlue New York storm-shutdown finder.

Reads BTS "Reporting Carrier On-Time Performance" CSV files and, for each day,
works out what share of JetBlue's New York flights were cancelled.
A "shutdown day" is a day when more than THRESHOLD of those flights were cancelled.

Usage:
    python jfk_storms.py path/to/folder_with_csvs_or_zips
"""

import sys
import glob
import os
import pandas as pd

AIRLINE = "B6"                                       # JetBlue's code in BTS data
NY_AIRPORTS = {"JFK", "LGA", "EWR", "HPN", "ISP"}    # the 10-K's "New York metro" airports
THRESHOLD = 0.50                                     # >50% cancelled = shutdown day


def load_files(folder):
    """Read every CSV (or zip containing a CSV) in the folder into one table."""
    paths = glob.glob(os.path.join(folder, "**", "*.csv"), recursive=True) + \
            glob.glob(os.path.join(folder, "**", "*.zip"), recursive=True)
    tables, seen_months = [], set()
    for p in sorted(paths):
        df = pd.read_csv(p, usecols=["FL_DATE", "OP_UNIQUE_CARRIER", "ORIGIN", "DEST", "CANCELLED", "CANCELLATION_CODE"])
        month = pd.to_datetime(df["FL_DATE"].iloc[0], format="mixed").strftime("%Y-%m")
        if month in seen_months:          # the same month downloaded twice: skip it
            print(f"Skipping duplicate file for {month}: {os.path.basename(p)}")
            continue
        seen_months.add(month)
        tables.append(df)
    return pd.concat(tables, ignore_index=True)


def daily_cancel_rates(df):
    """For each day: JetBlue flights touching New York, how many were cancelled, and the share."""
    df = df[df["OP_UNIQUE_CARRIER"] == AIRLINE].copy()
    df = df[df["ORIGIN"].isin(NY_AIRPORTS) | df["DEST"].isin(NY_AIRPORTS)]
    df["date"] = pd.to_datetime(df["FL_DATE"], format="mixed").dt.date
    df["weather_cxl"] = (df["CANCELLED"] == 1) & (df["CANCELLATION_CODE"] == "B")

    daily = df.groupby("date").agg(
        flights=("CANCELLED", "size"),
        cancelled=("CANCELLED", "sum"),
        weather_coded=("weather_cxl", "sum"),
    )
    daily["cancel_rate"] = daily["cancelled"] / daily["flights"]
    return daily


def find_shutdowns(daily, threshold=THRESHOLD):
    """Group back-to-back shutdown days into storm events."""
    # Only count days where most cancellations were coded as weather.
    # (This keeps out non-weather events, e.g. the COVID schedule cuts of March 2020.)
    weather_share = daily["weather_coded"] / daily["cancelled"].where(daily["cancelled"] > 0)
    bad = daily[(daily["cancel_rate"] > threshold) & (weather_share > 0.5)].index.tolist()
    events, current = [], []
    for d in bad:
        if current and (pd.Timestamp(d) - pd.Timestamp(current[-1])).days > 1:
            events.append(current)
            current = []
        current.append(d)
    if current:
        events.append(current)
    return events


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "."
    daily = daily_cancel_rates(load_files(folder))

    print("Worst 5 days for JetBlue in New York:")
    print(daily.sort_values("cancel_rate", ascending=False).head(5).to_string())
    print()

    # Show which months are loaded, so gaps in the data are visible
    months = sorted({(d.year, d.month) for d in daily.index})
    print("Months loaded:", ", ".join(f"{y}-{m:02d}" for y, m in months))
    print()

    # Try two thresholds to see how sensitive the count is
    for t in (THRESHOLD, 0.30):
        events = find_shutdowns(daily, t)
        print(f"Weather shutdown events (>{t:.0%} of JetBlue NY flights cancelled, mostly weather-coded):")
        for e in events:
            peak = daily.loc[e, "cancel_rate"].max()
            print(f"  {e[0]} to {e[-1]}  ({len(e)} day{'s' if len(e) > 1 else ''}, worst day {peak:.0%})")
        if not events:
            print("  none")
        print()
