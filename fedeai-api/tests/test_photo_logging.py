from io import BytesIO

from app.main import app


def test_photo_endpoint_logs_food_with_user_scope(client, monkeypatch):
    async def fake_estimator(image_bytes: bytes, caption: str | None = None):
        return {
            "meal_type": "dinner",
            "food_item": "mock chicken bowl",
            "calories": 620,
            "protein_g": 45,
            "carbs_g": 55,
            "fat_g": 22,
            "notes": "mocked from image",
        }

    monkeypatch.setattr("app.main.estimate_meal_from_image", fake_estimator)
    files = {"photo": ("meal.jpg", BytesIO(b"fake-jpg").read(), "image/jpeg")}
    data = {"caption": "my lunch"}
    headers = {"X-Telegram-User-Id": "777"}
    response = client.post("/api/tools/log-food-photo", files=files, data=data, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["tool"] == "log_food"
