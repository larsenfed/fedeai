from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from sqlalchemy.orm import Session

from . import models, schemas
from .config import settings
from .database import Base, engine, get_db
from .services.telegram import send_telegram_message
from .services.meal_vision import estimate_meal_from_image
from .services.telegram import get_file_bytes
from .services.tool_router import (
    build_calorie_chart,
    build_macro_chart,
    build_weight_chart,
    get_goals,
    get_reminder_preferences,
    log_food,
    log_weight,
    route_free_text,
    upsert_goals,
    upsert_reminder_preferences,
)

app = FastAPI(title="fedeai-api")
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"ok": True, "env": settings.app_env}


def get_current_user_ref(x_telegram_user_id: str | None = Header(default=None)) -> str:
    if not x_telegram_user_id:
        raise HTTPException(status_code=401, detail="Missing X-Telegram-User-Id header")
    return x_telegram_user_id


@app.post("/api/messages", response_model=schemas.ToolResponse)
def process_message(
    payload: schemas.ToolRequest,
    user_ref: str = Depends(get_current_user_ref),
    db: Session = Depends(get_db),
):
    return route_free_text(db, user_ref, payload.text)


@app.post("/api/tools/log-weight", response_model=schemas.ToolResponse)
def api_log_weight(
    payload: schemas.WeightLogRequest,
    user_ref: str = Depends(get_current_user_ref),
    db: Session = Depends(get_db),
):
    return log_weight(db, user_ref, payload.weight_kg, payload.log_date, payload.notes)


@app.post("/api/tools/log-food", response_model=schemas.ToolResponse)
def api_log_food(
    payload: schemas.FoodLogRequest,
    user_ref: str = Depends(get_current_user_ref),
    db: Session = Depends(get_db),
):
    return log_food(
        db=db,
        user_ref=user_ref,
        meal_type=payload.meal_type,
        food_item=payload.food_item,
        calories=payload.calories,
        protein_g=payload.protein_g,
        carbs_g=payload.carbs_g,
        fat_g=payload.fat_g,
        log_date=payload.log_date,
        notes=payload.notes,
    )


@app.post("/api/tools/charts", response_model=schemas.ToolResponse)
def api_chart(
    payload: schemas.ChartRequest,
    user_ref: str = Depends(get_current_user_ref),
    db: Session = Depends(get_db),
):
    if payload.chart_type == "weight_trend":
        return build_weight_chart(db, user_ref, payload.days)
    if payload.chart_type == "calorie_trend":
        return build_calorie_chart(db, user_ref, payload.days)
    return build_macro_chart(db, user_ref, payload.days)


@app.post("/api/tools/log-food-photo", response_model=schemas.ToolResponse)
async def api_log_food_photo(
    photo: UploadFile = File(...),
    caption: str | None = Form(default=None),
    user_ref: str = Depends(get_current_user_ref),
    db: Session = Depends(get_db),
):
    image_bytes = await photo.read()
    estimated = await estimate_meal_from_image(image_bytes, caption=caption)
    return log_food(
        db=db,
        user_ref=user_ref,
        meal_type=estimated["meal_type"],
        food_item=estimated["food_item"],
        calories=estimated["calories"],
        protein_g=estimated["protein_g"],
        carbs_g=estimated["carbs_g"],
        fat_g=estimated["fat_g"],
        notes=estimated.get("notes"),
    )


@app.put("/api/goals", response_model=schemas.GoalResponse)
def api_set_goals(
    payload: schemas.GoalUpsertRequest,
    user_ref: str = Depends(get_current_user_ref),
    db: Session = Depends(get_db),
):
    goal = upsert_goals(
        db=db,
        user_ref=user_ref,
        target_weight_kg=payload.target_weight_kg,
        daily_calorie_target=payload.daily_calorie_target,
        protein_target_g=payload.protein_target_g,
        carbs_target_g=payload.carbs_target_g,
        fat_target_g=payload.fat_target_g,
        weekly_weight_delta_kg=payload.weekly_weight_delta_kg,
    )
    return schemas.GoalResponse(
        target_weight_kg=goal.target_weight_kg,
        daily_calorie_target=goal.daily_calorie_target,
        protein_target_g=goal.protein_target_g,
        carbs_target_g=goal.carbs_target_g,
        fat_target_g=goal.fat_target_g,
        weekly_weight_delta_kg=goal.weekly_weight_delta_kg,
    )


@app.get("/api/goals", response_model=schemas.GoalResponse)
def api_get_goals(
    user_ref: str = Depends(get_current_user_ref),
    db: Session = Depends(get_db),
):
    goal = get_goals(db, user_ref)
    if not goal:
        return schemas.GoalResponse()
    return schemas.GoalResponse(
        target_weight_kg=goal.target_weight_kg,
        daily_calorie_target=goal.daily_calorie_target,
        protein_target_g=goal.protein_target_g,
        carbs_target_g=goal.carbs_target_g,
        fat_target_g=goal.fat_target_g,
        weekly_weight_delta_kg=goal.weekly_weight_delta_kg,
    )


@app.put("/api/reminders", response_model=schemas.ReminderPreferenceResponse)
def api_set_reminders(
    payload: schemas.ReminderPreferenceUpsert,
    user_ref: str = Depends(get_current_user_ref),
    db: Session = Depends(get_db),
):
    pref = upsert_reminder_preferences(
        db=db,
        user_ref=user_ref,
        timezone=payload.timezone,
        remind_food=payload.remind_food,
        remind_weight=payload.remind_weight,
        remind_weekly_summary=payload.remind_weekly_summary,
        food_time_local=payload.food_time_local,
        weight_time_local=payload.weight_time_local,
        weekly_summary_day=payload.weekly_summary_day,
        weekly_summary_time_local=payload.weekly_summary_time_local,
    )
    return schemas.ReminderPreferenceResponse(
        timezone=pref.timezone,
        remind_food=pref.remind_food,
        remind_weight=pref.remind_weight,
        remind_weekly_summary=pref.remind_weekly_summary,
        food_time_local=pref.food_time_local,
        weight_time_local=pref.weight_time_local,
        weekly_summary_day=pref.weekly_summary_day,
        weekly_summary_time_local=pref.weekly_summary_time_local,
    )


@app.get("/api/reminders", response_model=schemas.ReminderPreferenceResponse)
def api_get_reminders(
    user_ref: str = Depends(get_current_user_ref),
    db: Session = Depends(get_db),
):
    pref = get_reminder_preferences(db, user_ref)
    if not pref:
        return schemas.ReminderPreferenceResponse()
    return schemas.ReminderPreferenceResponse(
        timezone=pref.timezone,
        remind_food=pref.remind_food,
        remind_weight=pref.remind_weight,
        remind_weekly_summary=pref.remind_weekly_summary,
        food_time_local=pref.food_time_local,
        weight_time_local=pref.weight_time_local,
        weekly_summary_day=pref.weekly_summary_day,
        weekly_summary_time_local=pref.weekly_summary_time_local,
    )


@app.post("/webhook/telegram")
async def telegram_webhook(
    update: dict,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    message = update.get("message") or {}
    chat = message.get("chat") or {}
    from_user = message.get("from") or {}
    text = message.get("text", "")
    chat_id = str(chat.get("id", ""))
    user_ref = str(from_user.get("id", chat_id))
    photo_list = message.get("photo") or []
    if not chat_id:
        return {"ok": True, "ignored": True}

    if photo_list:
        best_photo = sorted(photo_list, key=lambda p: p.get("file_size", 0), reverse=True)[0]
        file_id = best_photo.get("file_id")
        if not file_id:
            await send_telegram_message(chat_id, "Could not read photo metadata.")
            return {"ok": True}
        try:
            image_bytes = await get_file_bytes(file_id)
            estimated = await estimate_meal_from_image(image_bytes, caption=text or None)
            result = log_food(
                db=db,
                user_ref=user_ref,
                meal_type=estimated["meal_type"],
                food_item=estimated["food_item"],
                calories=estimated["calories"],
                protein_g=estimated["protein_g"],
                carbs_g=estimated["carbs_g"],
                fat_g=estimated["fat_g"],
                notes=estimated.get("notes"),
            )
            result.message = (
                f"Meal logged: {estimated['food_item']} | "
                f"{estimated['calories']} kcal | "
                f"P {estimated['protein_g']:.0f}g C {estimated['carbs_g']:.0f}g F {estimated['fat_g']:.0f}g"
            )
        except Exception as exc:
            result = schemas.ToolResponse(tool="log_food_photo", ok=False, message=f"Photo analysis failed: {exc}")
    else:
        if not text:
            return {"ok": True, "ignored": True}
        result = route_free_text(db, user_ref=user_ref, text=text)
    await send_telegram_message(chat_id, result.message)
    return {"ok": True}
