from pathlib import Path


def test_webhook_chart_response_sends_photo(client, monkeypatch, tmp_path):
    chart_file = tmp_path / "calorie_chart.png"
    chart_file.write_bytes(b"fake-png-bytes")

    def fake_route_free_text(db, user_ref: str, text: str):
        from app.schemas import ToolResponse

        return ToolResponse(
            tool="chart_calories",
            ok=True,
            message="Calorie chart generated.",
            output_path=str(chart_file),
        )

    sent = {"photo": 0, "message": 0}

    async def fake_send_photo(chat_id: str, photo_bytes: bytes, caption: str | None = None):
        sent["photo"] += 1
        assert chat_id == "7216949028"
        assert photo_bytes == b"fake-png-bytes"
        assert "Calorie chart generated." in (caption or "")

    async def fake_send_message(chat_id: str, text: str):
        sent["message"] += 1

    monkeypatch.setattr("app.main.route_free_text", fake_route_free_text)
    monkeypatch.setattr("app.main.send_telegram_photo", fake_send_photo)
    monkeypatch.setattr("app.main.send_telegram_message", fake_send_message)

    payload = {
        "message": {
            "chat": {"id": 7216949028},
            "from": {"id": 7216949028},
            "text": "health give me a chart of calories per day this week",
        }
    }
    response = client.post(
        "/webhook/telegram",
        json=payload,
        headers={"x-telegram-bot-api-secret-token": "test-secret"},
    )
    assert response.status_code == 200
    assert sent["photo"] == 1
    assert sent["message"] == 0
