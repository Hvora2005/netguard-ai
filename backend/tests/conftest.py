"""Points the app at a throwaway SQLite DB + storage dirs before any app
module is imported, so running the test suite never touches your real
netguard.db, uploads/, models_storage/, or reports/.
"""

import os
import tempfile
from pathlib import Path

_TEST_DIR = Path(tempfile.mkdtemp(prefix="netguard_test_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TEST_DIR / 'test.db').as_posix()}"
os.environ["UPLOAD_PATH"] = str(_TEST_DIR / "uploads")
os.environ["MODEL_STORAGE_PATH"] = str(_TEST_DIR / "models_storage")
os.environ["REPORTS_PATH"] = str(_TEST_DIR / "reports")
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
