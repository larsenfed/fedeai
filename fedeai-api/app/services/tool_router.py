import re
from datetime import date, datetime
from pathlib import Path

import matplotlib.pyplot as plt
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..schemas import ToolResponse


CHART_DIR = Path("charts")
CHART_DIR.mkdir(parents=True, exist_ok=True)


def get_or_create_user(db: Session, user_ref: str) -> models.User:
    existing = db.scalar(select(models.User).where(models.User.telegram_user_id == user_ref))
    if existing:
        return existing
    user = models.User(telegram_user_id=user_ref)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def log_weight(db: Session, user_ref: str, weight_kg: float, log_date: date | None = None, notes: str | None = None) -> ToolResponse:
    user = get_or_create_user(db, user_ref)
    entry = models.WeightLog(
        user_id=user.id,
        log_date=log_date or date.today(),
        weight_kg=weight_kg,
        notes=notes,
    )
    db.add(entry)
    db.commit()
    return ToolResponse(tool="log_weight", ok=True, message=f"Weight logged: {weight_kg} kg")


def log_food(
    db: Session,
    user_ref: str,
    meal_type: str,
    food_item: str,
    calories: int,
    protein_g: float,
    carbs_g: float,
    fat_g: float,
    log_date: date | None = None,
    notes: str | None = None,
) -> ToolResponse:
    user = get_or_create_user(db, user_ref)
    entry = models.FoodLog(
        user_id=user.id,
        log_date=log_date or date.today(),
        meal_type=meal_type,
        food_item=food_item,
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        notes=notes,
    )
    db.add(entry)
    db.commit()
    return ToolResponse(tool="log_food", ok=True, message=f"Food logged: {food_item}")


def build_weight_chart(db: Session, user_ref: str, days: int = 30) -> ToolResponse:
    user = get_or_create_user(db, user_ref)
    rows = db.scalars(
        select(models.WeightLog)
        .where(models.WeightLog.user_id == user.id)
        .order_by(models.WeightLog.log_date.desc())
        .limit(days)
    ).all()
    rows = list(reversed(rows))
    if not rows:
        return ToolResponse(tool="chart_weight", ok=False, message="No weight data yet.")

    x = [r.log_date.isoformat() for r in rows]
    y = [r.weight_kg for r in rows]
    plt.figure(figsize=(8, 4))
    plt.plot(x, y, marker="o")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.title("Weight Trend")
    plt.ylabel("kg")
    output = CHART_DIR / f"weight_trend_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(output)
    plt.close()
    return ToolResponse(tool="chart_weight", ok=True, message="Weight chart generated.", output_path=str(output))


def build_macro_chart(db: Session, user_ref: str, days: int = 7) -> ToolResponse:
    user = get_or_create_user(db, user_ref)
    rows = db.scalars(
        select(models.FoodLog)
        .where(models.FoodLog.user_id == user.id)
        .order_by(models.FoodLog.log_date.desc())
        .limit(days * 10)
    ).all()
    if not rows:
        return ToolResponse(tool="chart_macro", ok=False, message="No food data yet.")
    protein = sum(r.protein_g for r in rows)
    carbs = sum(r.carbs_g for r in rows)
    fat = sum(r.fat_g for r in rows)
    values = [protein, carbs, fat]
    if sum(values) == 0:
        return ToolResponse(tool="chart_macro", ok=False, message="Macro totals are zero.")

    plt.figure(figsize=(5, 5))
    plt.pie(values, labels=["Protein", "Carbs", "Fat"], autopct="%1.1f%%")
    plt.title("Macro Distribution")
    output = CHART_DIR / f"macro_pie_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(output)
    plt.close()
    return ToolResponse(tool="chart_macro", ok=True, message="Macro chart generated.", output_path=str(output))


def route_free_text(db: Session, user_ref: str, text: str) -> ToolResponse:
    lower = text.lower()
    weight_match = re.search(r"(\d+(?:[.,]\d+)?)\s*kg", lower)
    if "/weight" in lower or "weight" in lower or weight_match:
        if not weight_match:
            return ToolResponse(tool="log_weight", ok=False, message="Weight value missing. Example: 77.7 kg")
        value = float(weight_match.group(1).replace(",", "."))
        return log_weight(db, user_ref, value, notes="Logged from free text")

    if "chart" in lower or "trend" in lower or "graph" in lower:
        if "weight" in lower:
            return build_weight_chart(db, user_ref)
        return build_macro_chart(db, user_ref)

    if "meal" in lower or "food" in lower or "calories" in lower:
        return ToolResponse(tool="log_food", ok=False, message="Use /api/tools/log-food with structured macros.")

    return ToolResponse(tool="unknown", ok=False, message="Could not map message to a tool.")


def upsert_goals(
    db: Session,
    user_ref: str,
    target_weight_kg: float | None = None,
    daily_calorie_target: int | None = None,
    protein_target_g: float | None = None,
    carbs_target_g: float | None = None,
    fat_target_g: float | None = None,
    weekly_weight_delta_kg: float | None = None,
) -> models.UserGoal:
    user = get_or_create_user(db, user_ref)
    goal = db.scalar(select(models.UserGoal).where(models.UserGoal.user_id == user.id))
    if not goal:
        goal = models.UserGoal(user_id=user.id)
        db.add(goal)
    goal.target_weight_kg = target_weight_kg
    goal.daily_calorie_target = daily_calorie_target
    goal.protein_target_g = protein_target_g
    goal.carbs_target_g = carbs_target_g
    goal.fat_target_g = fat_target_g
    goal.weekly_weight_delta_kg = weekly_weight_delta_kg
    db.commit()
    db.refresh(goal)
    return goal


def get_goals(db: Session, user_ref: str) -> models.UserGoal | None:
    user = get_or_create_user(db, user_ref)
    return db.scalar(select(models.UserGoal).where(models.UserGoal.user_id == user.id))


def upsert_reminder_preferences(
    db: Session,
    user_ref: str,
    timezone: str,
    remind_food: bool,
    remind_weight: bool,
    remind_weekly_summary: bool,
    food_time_local: str,
    weight_time_local: str,
    weekly_summary_day: str,
    weekly_summary_time_local: str,
) -> models.ReminderPreference:
    user = get_or_create_user(db, user_ref)
    pref = db.scalar(select(models.ReminderPreference).where(models.ReminderPreference.user_id == user.id))
    if not pref:
        pref = models.ReminderPreference(user_id=user.id)
        db.add(pref)
    pref.timezone = timezone
    pref.remind_food = remind_food
    pref.remind_weight = remind_weight
    pref.remind_weekly_summary = remind_weekly_summary
    pref.food_time_local = food_time_local
    pref.weight_time_local = weight_time_local
    pref.weekly_summary_day = weekly_summary_day
    pref.weekly_summary_time_local = weekly_summary_time_local
    db.commit()
    db.refresh(pref)
    return pref


def get_reminder_preferences(db: Session, user_ref: str) -> models.ReminderPreference | None:
    user = get_or_create_user(db, user_ref)
    return db.scalar(select(models.ReminderPreference).where(models.ReminderPreference.user_id == user.id))
