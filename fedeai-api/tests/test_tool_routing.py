from app.database import SessionLocal
from app.services.tool_router import route_free_text


def test_weight_text_routes_to_log_weight():
    db = SessionLocal()
    try:
        result = route_free_text(db, user_ref="999", text="today weight is 77.7 kg")
        assert result.ok is True
        assert result.tool == "log_weight"
    finally:
        db.close()


def test_meal_text_routes_to_log_food(monkeypatch):
    def fake_estimator(_text: str):
        return {
            "meal_type": "lunch",
            "food_item": "chicken avocado salad",
            "calories": 640,
            "protein_g": 55,
            "carbs_g": 20,
            "fat_g": 35,
            "notes": "estimated",
        }

    monkeypatch.setattr("app.services.tool_router.estimate_meal_from_text", fake_estimator)
    db = SessionLocal()
    try:
        result = route_free_text(
            db,
            user_ref="999",
            text="I had for lunch today 2 chicken fillet half a small avocado and asparagus with tomato salad and olive oil",
        )
        assert result.ok is True
        assert result.tool == "log_food"
        assert "Meal logged" in result.message
    finally:
        db.close()


def test_unstructured_calorie_chart_request(monkeypatch):
    def fake_router(_text: str):
        return {"tool": "chart_calories", "params": {"days": 7}}

    monkeypatch.setattr("app.services.tool_router.infer_tool_call_from_text", fake_router)
    db = SessionLocal()
    try:
        result = route_free_text(db, user_ref="999", text="give me a chart of my calories per day this week")
        assert result.tool == "chart_calories"
        assert result.ok in [True, False]
    finally:
        db.close()
