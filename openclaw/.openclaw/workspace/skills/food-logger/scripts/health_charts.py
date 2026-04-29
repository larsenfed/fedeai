#!/usr/bin/env python3
import argparse
import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta

try:
    import matplotlib.pyplot as plt
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "matplotlib is required for chart generation. "
        "Install it with: pip3 install matplotlib"
    ) from exc


DATA_DIR = os.path.expanduser("~/.openclaw/agents/main/food-logger/data/nutrition")
FOOD_CSV = os.path.join(DATA_DIR, "food_log.csv")
WEIGHT_CSV = os.path.join(DATA_DIR, "weight_log.csv")
CHARTS_DIR = os.path.join(DATA_DIR, "charts")


def ensure_paths():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(CHARTS_DIR, exist_ok=True)


def _load_food_rows():
    if not os.path.exists(FOOD_CSV):
        return []
    with open(FOOD_CSV, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_weight_rows():
    if not os.path.exists(WEIGHT_CSV):
        return []
    with open(WEIGHT_CSV, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def macro_pie(days=7):
    ensure_paths()
    today = datetime.now().date()
    start = today - timedelta(days=days - 1)

    totals = defaultdict(float)
    for row in _load_food_rows():
        try:
            d = datetime.strptime(row["date"], "%Y-%m-%d").date()
            if d >= start:
                totals["Protein"] += float(row.get("protein_g", 0) or 0)
                totals["Carbs"] += float(row.get("carbs_g", 0) or 0)
                totals["Fat"] += float(row.get("fat_g", 0) or 0)
        except (ValueError, KeyError):
            continue

    values = [totals["Protein"], totals["Carbs"], totals["Fat"]]
    if sum(values) <= 0:
        raise SystemExit("No macro data available for the selected range.")

    labels = ["Protein", "Carbs", "Fat"]
    colors = ["#4CAF50", "#2196F3", "#FF9800"]

    fig, ax = plt.subplots(figsize=(6, 6), dpi=140)
    ax.pie(
        values,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    ax.set_title(f"Macro Distribution - Last {days} Days")
    ax.axis("equal")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = os.path.join(CHARTS_DIR, f"macro_pie_{stamp}.png")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out


def weight_timeseries(days=30):
    ensure_paths()
    rows = []
    for row in _load_weight_rows():
        try:
            rows.append(
                (
                    datetime.strptime(row["date"], "%Y-%m-%d").date(),
                    float(row["weight_kg"]),
                )
            )
        except (ValueError, KeyError, TypeError):
            continue

    rows.sort(key=lambda x: x[0])
    if days > 0:
        rows = rows[-days:]

    if not rows:
        raise SystemExit("No weight data available for the selected range.")

    x = [d.strftime("%Y-%m-%d") for d, _ in rows]
    y = [w for _, w in rows]

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=140)
    ax.plot(x, y, marker="o", color="#7E57C2", linewidth=2)
    ax.set_title("Weight Trend")
    ax.set_xlabel("Date")
    ax.set_ylabel("Weight (kg)")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.tick_params(axis="x", rotation=45)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = os.path.join(CHARTS_DIR, f"weight_trend_{stamp}.png")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("macro-pie")
    p.add_argument("--days", type=int, default=7)

    p = sub.add_parser("weight-timeseries")
    p.add_argument("--days", type=int, default=30)

    args = parser.parse_args()
    if args.command == "macro-pie":
        print(macro_pie(days=args.days))
    elif args.command == "weight-timeseries":
        print(weight_timeseries(days=args.days))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
