import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.core.testing import make_settings
from app.main import build_app

@pytest.fixture()
def client():
    with TestClient(build_app(make_settings())) as c:
        yield c
