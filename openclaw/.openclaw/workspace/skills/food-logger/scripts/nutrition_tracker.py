#!/usr/bin/env python3
import argparse
import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta

DATA_DIR = os.path.expanduser("~/.openclaw/agents/main/food-logger/data/nutrition")
FOOD_CSV = os.path.join(DATA_DIR, "food_log.csv")
WEIGHT_CSV = os.path.join(DATA_DIR, "weight_log.csv")


def ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(FOOD_CSV):
        with open(FOOD_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                [
                    "date",
                    "meal_type",
                    "food_item",
                    "calories",
                    "protein_g",
                    "carbs_g",
                    "fat_g",
                    "notes",
                ]
            )
    if not os.path.exists(WEIGHT_CSV):
        with open(WEIGHT_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["date", "weight_kg", "notes"])


def parse_date(date_str):
    datetime.strptime(date_str, "%Y-%m-%d")
    return date_str


def add_food(date, meal_type, food_item, calories, protein, carbs, fat, notes=""):
    ensure_files()
    with open(FOOD_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([date, meal_type, food_item, calories, protein, carbs, fat, notes])
    print(f"Added food: {food_item} ({calories} kcal)")


def add_weight(date, weight_kg, notes=""):
    ensure_files()
    with open(WEIGHT_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([date, weight_kg, notes])
    print(f"Added weight: {weight_kg} kg")


def get_summary(days=7):
    ensure_files()
    today = datetime.now().date()
    start = today - timedelta(days=days - 1)
    daily = defaultdict(lambda: {"cal": 0, "pro": 0.0, "car": 0.0, "fat": 0.0})

    with open(FOOD_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                row_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                if row_date >= start:
                    d = row["date"]
                    daily[d]["cal"] += int(float(row["calories"]))
                    daily[d]["pro"] += float(row["protein_g"])
                    daily[d]["car"] += float(row["carbs_g"])
                    daily[d]["fat"] += float(row["fat_g"])
            except (ValueError, KeyError):
                # Skip malformed rows instead of crashing on bad historical data.
                continue

    print(f"\nNutrition Summary (last {days} days)")
    if not daily:
        print("No food entries found in this period.")
        return

    for d in sorted(daily.keys()):
        v = daily[d]
        print(f"{d}: {v['cal']} kcal | P:{v['pro']:.1f}g C:{v['car']:.1f}g F:{v['fat']:.1f}g")

    total_cal = sum(v["cal"] for v in daily.values())
    avg_cal = total_cal / len(daily)
    print(f"\nTotals: {total_cal} kcal | Avg/day: {avg_cal:.0f} kcal")


def get_weight_trend(days=30):
    ensure_files()
    data = []
    with open(WEIGHT_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("date"):
                data.append(row)

    data.sort(key=lambda x: x["date"])
    print(f"\nWeight Trend (last {days} entries)")
    if not data:
        print("No weight entries found.")
        return

    for row in data[-days:]:
        notes = row.get("notes", "").strip()
        suffix = f" ({notes})" if notes else ""
        print(f"{row['date']}: {row['weight_kg']} kg{suffix}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")

    food_parser = sub.add_parser("add-food")
    food_parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    food_parser.add_argument("--meal", required=True)
    food_parser.add_argument("--food", required=True)
    food_parser.add_argument("--calories", type=int, required=True)
    food_parser.add_argument("--protein", type=float, required=True)
    food_parser.add_argument("--carbs", type=float, required=True)
    food_parser.add_argument("--fat", type=float, required=True)
    food_parser.add_argument("--notes", default="")

    weight_parser = sub.add_parser("add-weight")
    weight_parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    weight_parser.add_argument("--weight", type=float, required=True)
    weight_parser.add_argument("--notes", default="")

    summary_parser = sub.add_parser("summary")
    summary_parser.add_argument("--days", type=int, default=7)

    trend_parser = sub.add_parser("weight-trend")
    trend_parser.add_argument("--days", type=int, default=30)

    args = parser.parse_args()

    if args.command == "add-food":
        add_food(
            parse_date(args.date),
            args.meal,
            args.food,
            args.calories,
            args.protein,
            args.carbs,
            args.fat,
            args.notes,
        )
    elif args.command == "add-weight":
        add_weight(parse_date(args.date), args.weight, args.notes)
    elif args.command == "summary":
        get_summary(args.days)
    elif args.command == "weight-trend":
        get_weight_trend(args.days)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()