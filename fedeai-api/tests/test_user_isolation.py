def test_requires_user_header(client):
    response = client.post("/api/messages", json={"text": "77.7 kg"})
    assert response.status_code == 401


def test_data_isolation_by_user_header(client):
    user_a = {"X-Telegram-User-Id": "111"}
    user_b = {"X-Telegram-User-Id": "222"}

    goal_payload = {
        "target_weight_kg": 73.0,
        "daily_calorie_target": 1900,
        "protein_target_g": 180,
        "carbs_target_g": 100,
        "fat_target_g": 60,
        "weekly_weight_delta_kg": -0.6,
    }
    set_goal = client.put("/api/goals", json=goal_payload, headers=user_a)
    assert set_goal.status_code == 200

    goal_a = client.get("/api/goals", headers=user_a)
    goal_b = client.get("/api/goals", headers=user_b)
    assert goal_a.status_code == 200
    assert goal_b.status_code == 200
    assert goal_a.json()["target_weight_kg"] == 73.0
    assert goal_b.json()["target_weight_kg"] is None
