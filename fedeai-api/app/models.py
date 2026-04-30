from datetime import datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    food_logs: Mapped[list["FoodLog"]] = relationship(back_populates="user")
    weight_logs: Mapped[list["WeightLog"]] = relationship(back_populates="user")
    goals: Mapped[list["UserGoal"]] = relationship(back_populates="user")
    reminder_prefs: Mapped[list["ReminderPreference"]] = relationship(back_populates="user")


class FoodLog(Base):
    __tablename__ = "food_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    log_date: Mapped[Date] = mapped_column(Date, index=True)
    meal_type: Mapped[str] = mapped_column(String(32))
    food_item: Mapped[str] = mapped_column(String(255))
    calories: Mapped[int] = mapped_column(Integer)
    protein_g: Mapped[float] = mapped_column(Float)
    carbs_g: Mapped[float] = mapped_column(Float)
    fat_g: Mapped[float] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="food_logs")


class WeightLog(Base):
    __tablename__ = "weight_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    log_date: Mapped[Date] = mapped_column(Date, index=True)
    weight_kg: Mapped[float] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="weight_logs")


class UserGoal(Base):
    __tablename__ = "user_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    target_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    daily_calorie_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protein_target_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_target_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_target_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    weekly_weight_delta_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="goals")


class ReminderPreference(Base):
    __tablename__ = "reminder_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    remind_food: Mapped[bool] = mapped_column(default=True)
    remind_weight: Mapped[bool] = mapped_column(default=True)
    remind_weekly_summary: Mapped[bool] = mapped_column(default=True)
    food_time_local: Mapped[str] = mapped_column(String(5), default="20:30")
    weight_time_local: Mapped[str] = mapped_column(String(5), default="07:00")
    weekly_summary_day: Mapped[str] = mapped_column(String(9), default="Sunday")
    weekly_summary_time_local: Mapped[str] = mapped_column(String(5), default="20:00")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="reminder_prefs")
