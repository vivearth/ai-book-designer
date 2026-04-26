import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

DB_PATH = Path('data/test_book_designer.db')
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if DB_PATH.exists():
    DB_PATH.unlink()
os.environ['DATABASE_URL'] = f"sqlite:///{DB_PATH}"
os.environ['MODEL_PROVIDER'] = 'mock'

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
