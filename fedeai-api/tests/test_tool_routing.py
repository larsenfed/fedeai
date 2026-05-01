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


def test_food_log_message_includes_goal_tracking(monkeypatch):
    def fake_router(_text: str):
        return {
            "tool": "log_food",
            "params": {
                "meal_type": "lunch",
                "food_item": "chicken salad",
                "calories": 600,
                "protein_g": 45,
                "carbs_g": 25,
                "fat_g": 28,
            },
        }

    monkeypatch.setattr("app.services.tool_router.infer_tool_call_from_text", fake_router)
    db = SessionLocal()
    try:
        result = route_free_text(db, user_ref="999", text="I had chicken salad for lunch")
        assert result.ok is True
        assert "Today total" in result.message
        assert "Last 7 days" in result.message
    finally:
        db.close()


def test_unstructured_weight_via_ai_tool_mapping(monkeypatch):
    def fake_router(_text: str):
        return {"tool": "log_weight", "params": {"weight_kg": 77.2}}

    monkeypatch.setattr("app.services.tool_router.infer_tool_call_from_text", fake_router)
    db = SessionLocal()
    try:
        result = route_free_text(db, user_ref="999", text="today scale was around seventy seven point two")
        assert result.ok is True
        assert result.tool == "log_weight"
        assert "77.2" in result.message
    finally:
        db.close()


def test_log_food_with_past_date_from_ai(monkeypatch):
    def fake_router(_text: str):
        return {
            "tool": "log_food",
            "params": {
                "meal_type": "dinner",
                "food_item": "ensalada con pollo",
                "calories": 550,
                "protein_g": 42,
                "carbs_g": 18,
                "fat_g": 27,
                "log_date": "2026-04-30",
            },
        }

    monkeypatch.setattr("app.services.tool_router.infer_tool_call_from_text", fake_router)
    db = SessionLocal()
    try:
        result = route_free_text(db, user_ref="999", text="dinner last night chicken salad")
        assert result.ok is True
        assert result.tool == "log_food"
    finally:
        db.close()


def test_update_food_date_and_meal(monkeypatch):
    steps = iter(
        [
            {
                "tool": "log_food",
                "params": {
                    "meal_type": "breakfast",
                    "food_item": "ensalada",
                    "calories": 300,
                    "protein_g": 15,
                    "carbs_g": 20,
                    "fat_g": 15,
                },
            },
            {
                "tool": "update_food",
                "params": {
                    "food_item_contains": "ensalada",
                    "meal_type": "breakfast",
                    "to_date": "2026-04-30",
                    "to_meal_type": "dinner",
                },
            },
        ]
    )

    def fake_router(_text: str):
        return next(steps)

    monkeypatch.setattr("app.services.tool_router.infer_tool_call_from_text", fake_router)
    db = SessionLocal()
    try:
        _ = route_free_text(db, user_ref="999", text="log ensalada")
        result = route_free_text(db, user_ref="999", text="move that ensalada to yesterday dinner")
        assert result.ok is True
        assert result.tool == "update_food"
        assert "Updated food entry" in result.message
    finally:
        db.close()


def test_delete_food_entry(monkeypatch):
    steps = iter(
        [
            {
                "tool": "log_food",
                "params": {
                    "meal_type": "breakfast",
                    "food_item": "toast",
                    "calories": 200,
                    "protein_g": 8,
                    "carbs_g": 30,
                    "fat_g": 6,
                },
            },
            {
                "tool": "delete_food",
                "params": {"food_item_contains": "toast", "meal_type": "breakfast"},
            },
        ]
    )

    def fake_router(_text: str):
        return next(steps)

    monkeypatch.setattr("app.services.tool_router.infer_tool_call_from_text", fake_router)
    db = SessionLocal()
    try:
        _ = route_free_text(db, user_ref="999", text="log breakfast toast")
        result = route_free_text(db, user_ref="999", text="delete the breakfast it was a mistake")
        assert result.ok is True
        assert result.tool == "delete_food"
        assert "Deleted food entry" in result.message
    finally:
        db.close()


def test_update_food_uses_spanish_yesterday_from_text(monkeypatch):
    steps = iter(
        [
            {
                "tool": "log_food",
                "params": {
                    "meal_type": "lunch",
                    "food_item": "plato de ensalada campera",
                    "calories": 500,
                    "protein_g": 12,
                    "carbs_g": 55,
                    "fat_g": 20,
                },
            },
            {
                "tool": "update_food",
                "params": {
                    "food_item_contains": "ensalada campera",
                    "meal_type": "lunch",
                },
            },
        ]
    )

    def fake_router(_text: str):
        return next(steps)

    monkeypatch.setattr("app.services.tool_router.infer_tool_call_from_text", fake_router)
    db = SessionLocal()
    try:
        _ = route_free_text(db, user_ref="999", text="log ensalada")
        result = route_free_text(
            db,
            user_ref="999",
            text="mueve 1 plato de ensalada campera a la cena de ayer",
        )
        assert result.ok is True
        assert "dinner on" in result.message
    finally:
        db.close()


def test_update_food_uses_spanish_explicit_date(monkeypatch):
    steps = iter(
        [
            {
                "tool": "log_food",
                "params": {
                    "meal_type": "lunch",
                    "food_item": "plato de ensalada campera",
                    "calories": 500,
                    "protein_g": 12,
                    "carbs_g": 55,
                    "fat_g": 20,
                },
            },
            {
                "tool": "update_food",
                "params": {
                    "food_item_contains": "ensalada campera",
                    "meal_type": "lunch",
                },
            },
        ]
    )

    def fake_router(_text: str):
        return next(steps)

    monkeypatch.setattr("app.services.tool_router.infer_tool_call_from_text", fake_router)
    db = SessionLocal()
    try:
        _ = route_free_text(db, user_ref="999", text="log ensalada")
        result = route_free_text(
            db,
            user_ref="999",
            text="mueve 1 plato de ensalada campera a la cena de 30 de abril",
        )
        assert result.ok is True
        assert "-04-30" in result.message
    finally:
        db.close()
