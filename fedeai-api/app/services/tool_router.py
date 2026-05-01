import re
from datetime import date, datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..schemas import ToolResponse
from .meal_vision import estimate_meal_from_text, infer_tool_call_from_text


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
    return ToolResponse(tool="log_food", ok=True, message=_build_food_progress_message(db, user.id, food_item))


def _build_food_progress_message(db: Session, user_id: int, food_item: str) -> str:
    today = date.today()
    seven_days_ago = today - timedelta(days=6)

    today_rows = db.scalars(
        select(models.FoodLog).where(models.FoodLog.user_id == user_id, models.FoodLog.log_date == today)
    ).all()
    today_total = sum(int(r.calories) for r in today_rows)

    week_rows = db.scalars(
        select(models.FoodLog).where(models.FoodLog.user_id == user_id, models.FoodLog.log_date >= seven_days_ago)
    ).all()
    week_total = sum(int(r.calories) for r in week_rows)

    goal = db.scalar(select(models.UserGoal).where(models.UserGoal.user_id == user_id))
    daily_goal = goal.daily_calorie_target if goal and goal.daily_calorie_target else 1900
    weekly_budget = daily_goal * 7
    weekly_delta = weekly_budget - week_total

    if weekly_delta >= 0:
        trend = f"{weekly_delta} kcal remaining in your 7-day budget"
    else:
        trend = f"{abs(weekly_delta)} kcal over your 7-day budget"

    return (
        f"Food logged: {food_item}. "
        f"Today total: {today_total}/{daily_goal} kcal. "
        f"Last 7 days: {week_total}/{weekly_budget} kcal ({trend})."
    )


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


def build_calorie_chart(db: Session, user_ref: str, days: int = 7) -> ToolResponse:
    user = get_or_create_user(db, user_ref)
    rows = db.scalars(
        select(models.FoodLog)
        .where(models.FoodLog.user_id == user.id)
        .order_by(models.FoodLog.log_date.desc())
        .limit(days * 15)
    ).all()
    if not rows:
        return ToolResponse(tool="chart_calories", ok=False, message="No food data yet.")

    by_day: dict[str, int] = {}
    for r in rows:
        key = r.log_date.isoformat()
        by_day[key] = by_day.get(key, 0) + int(r.calories)
    days_sorted = sorted(by_day.keys())[-days:]
    calories = [by_day[d] for d in days_sorted]

    plt.figure(figsize=(8, 4))
    plt.bar(days_sorted, calories)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.title("Calories Per Day")
    plt.ylabel("kcal")
    output = CHART_DIR / f"calorie_trend_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(output)
    plt.close()
    return ToolResponse(tool="chart_calories", ok=True, message="Calorie chart generated.", output_path=str(output))


def route_free_text(db: Session, user_ref: str, text: str) -> ToolResponse:
    lower = text.lower()
    # AI-first tool mapping for unstructured text.
    try:
        ai_call = infer_tool_call_from_text(text)
        tool = ai_call.get("tool", "unknown")
        params = ai_call.get("params", {}) or {}

        if tool == "log_weight":
            w = params.get("weight_kg")
            if w is not None:
                return log_weight(
                    db,
                    user_ref,
                    float(w),
                    log_date=_parse_optional_date(params.get("log_date")),
                    notes="Logged from AI tool mapping",
                )

        if tool == "chart_weight":
            return build_weight_chart(db, user_ref, int(params.get("days", 30)))

        if tool == "chart_macro":
            return build_macro_chart(db, user_ref, int(params.get("days", 7)))

        if tool == "chart_calories":
            return build_calorie_chart(db, user_ref, int(params.get("days", 7)))

        if tool == "log_food":
            required = ["meal_type", "food_item", "calories", "protein_g", "carbs_g", "fat_g"]
            if all(k in params for k in required):
                return log_food(
                    db=db,
                    user_ref=user_ref,
                    meal_type=str(params["meal_type"]),
                    food_item=str(params["food_item"]),
                    calories=int(params["calories"]),
                    protein_g=float(params["protein_g"]),
                    carbs_g=float(params["carbs_g"]),
                    fat_g=float(params["fat_g"]),
                    log_date=_parse_optional_date(params.get("log_date")),
                    notes="Estimated from AI tool mapping",
                )

        if tool == "update_food":
            inferred_to_date = _parse_optional_date(params.get("to_date")) or _parse_date_from_text(text)
            inferred_to_meal = _safe_str(params.get("to_meal_type")) or _infer_meal_type_from_text(text)
            return update_food_entry(
                db=db,
                user_ref=user_ref,
                food_item_contains=_safe_str(params.get("food_item_contains")),
                meal_type=_safe_str(params.get("meal_type")),
                from_date=_parse_optional_date(params.get("from_date")),
                to_date=inferred_to_date,
                to_meal_type=inferred_to_meal,
            )

        if tool == "delete_food":
            return delete_food_entry(
                db=db,
                user_ref=user_ref,
                food_item_contains=_safe_str(params.get("food_item_contains")),
                meal_type=_safe_str(params.get("meal_type")),
                log_date=_parse_optional_date(params.get("log_date")),
            )
    except Exception:
        # Fallback to deterministic matching below.
        pass

    weight_match = re.search(r"(\d+(?:[.,]\d+)?)\s*kg", lower)
    if "/weight" in lower or "weight" in lower or weight_match:
        if not weight_match:
            return ToolResponse(tool="log_weight", ok=False, message="Weight value missing. Example: 77.7 kg")
        value = float(weight_match.group(1).replace(",", "."))
        return log_weight(db, user_ref, value, notes="Logged from free text")

    if "calorie" in lower and ("chart" in lower or "trend" in lower or "per day" in lower):
        days = 7 if "week" in lower else 30 if "month" in lower else 7
        return build_calorie_chart(db, user_ref, days=days)

    if "chart" in lower or "trend" in lower or "graph" in lower:
        if "weight" in lower:
            return build_weight_chart(db, user_ref)
        return build_macro_chart(db, user_ref)

    meal_signals = [
        "meal",
        "food",
        "calories",
        "breakfast",
        "lunch",
        "dinner",
        "snack",
        "had",
        "ate",
        "chicken",
        "avocado",
        "salad",
        "olive oil",
    ]
    if any(signal in lower for signal in meal_signals):
        try:
            estimated = estimate_meal_from_text(text)
            result = log_food(
                db=db,
                user_ref=user_ref,
                meal_type=estimated["meal_type"],
                food_item=estimated["food_item"],
                calories=estimated["calories"],
                protein_g=estimated["protein_g"],
                carbs_g=estimated["carbs_g"],
                fat_g=estimated["fat_g"],
                notes=estimated.get("notes", "Estimated from free text"),
            )
            result.message = (
                f"Meal logged: {estimated['food_item']} | "
                f"{estimated['calories']} kcal | "
                f"P {estimated['protein_g']:.0f}g C {estimated['carbs_g']:.0f}g F {estimated['fat_g']:.0f}g"
            )
            return result
        except Exception as exc:
            return ToolResponse(tool="log_food", ok=False, message=f"Could not parse meal text: {exc}")

    return ToolResponse(tool="unknown", ok=False, message="Could not map message to a tool.")


def _safe_str(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _parse_optional_date(v) -> date | None:
    if not v:
        return None
    if isinstance(v, date):
        return v
    try:
        return datetime.strptime(str(v), "%Y-%m-%d").date()
    except ValueError:
        return None


def _infer_meal_type_from_text(text: str) -> str | None:
    lower = text.lower()
    if any(k in lower for k in ["cena", "dinner"]):
        return "dinner"
    if any(k in lower for k in ["desayuno", "breakfast"]):
        return "breakfast"
    if any(k in lower for k in ["almuerzo", "comida", "lunch"]):
        return "lunch"
    if any(k in lower for k in ["snack", "merienda"]):
        return "snack"
    return None


def _parse_date_from_text(text: str) -> date | None:
    lower = text.lower()
    today = date.today()
    if any(k in lower for k in ["ayer", "yesterday", "anoche", "last night"]):
        return today - timedelta(days=1)
    if any(k in lower for k in ["hoy", "today"]):
        return today

    month_map = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }
    # Match "30 de abril" / "30 abril" / "april 30"
    day = None
    month = None
    for m in re.finditer(r"\b(\d{1,2})\s*(?:de\s+)?([a-zA-Záéíóúñ]+)\b", lower):
        d, mo = int(m.group(1)), m.group(2)
        mo = (
            mo.replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
            .replace("ñ", "n")
        )
        if mo in month_map:
            day, month = d, month_map[mo]
            break
    if day is None:
        for m in re.finditer(r"\b([a-zA-Záéíóúñ]+)\s+(\d{1,2})\b", lower):
            mo, d = m.group(1), int(m.group(2))
            mo = (
                mo.replace("á", "a")
                .replace("é", "e")
                .replace("í", "i")
                .replace("ó", "o")
                .replace("ú", "u")
                .replace("ñ", "n")
            )
            if mo in month_map:
                day, month = d, month_map[mo]
                break
    if day and month:
        year = today.year
        try:
            candidate = date(year, month, day)
        except ValueError:
            return None
        if candidate > today:
            candidate = date(year - 1, month, day)
        return candidate
    return None


def _find_food_candidate(
    db: Session,
    user_id: int,
    food_item_contains: str | None = None,
    meal_type: str | None = None,
    log_date: date | None = None,
):
    q = select(models.FoodLog).where(models.FoodLog.user_id == user_id)
    if food_item_contains:
        q = q.where(models.FoodLog.food_item.ilike(f"%{food_item_contains}%"))
    if meal_type:
        q = q.where(models.FoodLog.meal_type == meal_type)
    if log_date:
        q = q.where(models.FoodLog.log_date == log_date)
    q = q.order_by(models.FoodLog.created_at.desc())
    return db.scalar(q)


def update_food_entry(
    db: Session,
    user_ref: str,
    food_item_contains: str | None = None,
    meal_type: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    to_meal_type: str | None = None,
) -> ToolResponse:
    user = get_or_create_user(db, user_ref)
    entry = _find_food_candidate(
        db=db,
        user_id=user.id,
        food_item_contains=food_item_contains,
        meal_type=meal_type,
        log_date=from_date,
    )
    if not entry:
        return ToolResponse(tool="update_food", ok=False, message="No matching food record found to update.")

    if to_date:
        entry.log_date = to_date
    if to_meal_type:
        entry.meal_type = to_meal_type
    db.commit()
    return ToolResponse(
        tool="update_food",
        ok=True,
        message=f"Updated food entry: {entry.food_item} -> {entry.meal_type} on {entry.log_date.isoformat()}",
    )


def delete_food_entry(
    db: Session,
    user_ref: str,
    food_item_contains: str | None = None,
    meal_type: str | None = None,
    log_date: date | None = None,
) -> ToolResponse:
    user = get_or_create_user(db, user_ref)
    entry = _find_food_candidate(
        db=db,
        user_id=user.id,
        food_item_contains=food_item_contains,
        meal_type=meal_type,
        log_date=log_date,
    )
    if not entry:
        return ToolResponse(tool="delete_food", ok=False, message="No matching food record found to delete.")
    food_item = entry.food_item
    db.delete(entry)
    db.commit()
    return ToolResponse(tool="delete_food", ok=True, message=f"Deleted food entry: {food_item}")


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
