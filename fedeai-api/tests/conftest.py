import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("TELEGRAM_WEBHOOK_SECRET", "test-secret")
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)
