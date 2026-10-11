import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.seed.seed_data import seed_database

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_banking.db")
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Create tables and seed test data
    Base.metadata.create_all(bind=test_engine)
    # Ensure seed data exists
    seed_database(force_reset=False)
    yield
    # Cleanup test db
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
