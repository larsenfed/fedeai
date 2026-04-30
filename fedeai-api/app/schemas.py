from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ToolRequest(BaseModel):
    text: str


class WeightLogRequest(BaseModel):
    log_date: date
    weight_kg: float
    notes: str | None = None


class FoodLogRequest(BaseModel):
    log_date: date
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    food_item: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    notes: str | None = None


class ChartRequest(BaseModel):
    days: int = 7
    chart_type: Literal["macro_pie", "weight_trend", "calorie_trend"]


class GoalUpsertRequest(BaseModel):
    target_weight_kg: float | None = None
    daily_calorie_target: int | None = None
    protein_target_g: float | None = None
    carbs_target_g: float | None = None
    fat_target_g: float | None = None
    weekly_weight_delta_kg: float | None = None


class GoalResponse(BaseModel):
    target_weight_kg: float | None = None
    daily_calorie_target: int | None = None
    protein_target_g: float | None = None
    carbs_target_g: float | None = None
    fat_target_g: float | None = None
    weekly_weight_delta_kg: float | None = None


class ReminderPreferenceUpsert(BaseModel):
    timezone: str = "UTC"
    remind_food: bool = True
    remind_weight: bool = True
    remind_weekly_summary: bool = True
    food_time_local: str = "20:30"
    weight_time_local: str = "07:00"
    weekly_summary_day: str = "Sunday"
    weekly_summary_time_local: str = "20:00"


class ReminderPreferenceResponse(ReminderPreferenceUpsert):
    pass


class ToolResponse(BaseModel):
    tool: str
    ok: bool
    message: str
    output_path: str | None = None
