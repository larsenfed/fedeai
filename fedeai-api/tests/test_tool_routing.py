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
