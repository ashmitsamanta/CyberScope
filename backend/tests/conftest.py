import pytest
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, Base, SessionLocal
from app.models.case import Case
from scripts.seed_demo import seed_database
from app.services.graph_service import graph_service


@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    """
    Ensures that SQLite database tables are created and seeded
    before running the test suite.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        case_count = db.query(Case).count()
        if case_count == 0:
            seed_database(db_session=db, drop_existing=False)
        else:
            graph_service.sync_from_db(db)
    finally:
        db.close()
    yield
