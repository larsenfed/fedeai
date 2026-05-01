from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.database import SessionLocal
from app.models import FoodLog, ReminderPreference, User, WeightLog
from app.services.telegram import send_telegram_message


def _today_has_food(db, user_id: int) -> bool:
    return db.scalar(select(FoodLog).where(FoodLog.user_id == user_id, FoodLog.log_date == date.today())) is not None


def _today_has_meal_type(db, user_id: int, meal_type: str) -> bool:
    return (
        db.scalar(
            select(FoodLog).where(
                FoodLog.user_id == user_id,
                FoodLog.log_date == date.today(),
                FoodLog.meal_type == meal_type,
            )
        )
        is not None
    )


def _today_has_weight(db, user_id: int) -> bool:
    return db.scalar(select(WeightLog).where(WeightLog.user_id == user_id, WeightLog.log_date == date.today())) is not None


async def run_reminder_cycle() -> None:
    now = datetime.utcnow()
    db = SessionLocal()
    try:
        prefs = db.scalars(select(ReminderPreference)).all()
        for pref in prefs:
            user = db.scalar(select(User).where(User.id == pref.user_id))
            if not user:
                continue
            chat_id = user.telegram_user_id
            try:
                local_now = now.astimezone(ZoneInfo(pref.timezone))
            except Exception:
                local_now = now
            hhmm = local_now.strftime("%H:%M")

            if pref.remind_weight and pref.weight_time_local == hhmm and not _today_has_weight(db, user.id):
                await send_telegram_message(chat_id, "Reminder: log your morning weight today.")

            # Meal-specific reminders requested by user.
            if pref.remind_food and hhmm == "10:00" and not _today_has_meal_type(db, user.id, "breakfast"):
                await send_telegram_message(chat_id, "Reminder: you have not logged breakfast yet.")
            if pref.remind_food and hhmm == "14:00" and not _today_has_meal_type(db, user.id, "lunch"):
                await send_telegram_message(chat_id, "Reminder: you have not logged lunch yet.")
            if pref.remind_food and hhmm == "22:00" and not _today_has_meal_type(db, user.id, "dinner"):
                await send_telegram_message(chat_id, "Reminder: you have not logged dinner yet.")

            if pref.remind_weekly_summary and pref.weekly_summary_time_local == hhmm:
                if now.strftime("%A") == pref.weekly_summary_day:
                    await send_telegram_message(chat_id, "Weekly check-in: review your trend against your goals.")
    finally:
        db.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_reminder_cycle())
