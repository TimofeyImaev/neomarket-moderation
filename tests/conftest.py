"""Shared fixtures for moderation service tests."""
import uuid

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event as sa_event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db
from src.main import app
from src import config

# --- In-memory SQLite ----------------------------------------------------------
# StaticPool: all threads share the same underlying connection,
# so tables created in the test thread are visible to the request-handler thread.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@sa_event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# --- Auth helpers -------------------------------------------------------------
MODERATOR_ID = str(uuid.uuid4())
ANOTHER_MODERATOR_ID = str(uuid.uuid4())


def _make_token(moderator_id: str = MODERATOR_ID) -> str:
    return jwt.encode(
        {"sub": moderator_id, "role": "moderator", "exp": 9999999999},
        config.JWT_SECRET,
        algorithm=config.JWT_ALGORITHM,
    )


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {_make_token(MODERATOR_ID)}"}


@pytest.fixture
def other_auth_headers():
    return {"Authorization": f"Bearer {_make_token(ANOTHER_MODERATOR_ID)}"}


@pytest.fixture
def service_headers():
    return {"X-Service-Key": config.B2B_TO_MOD_KEY}


# --- Seed helpers -------------------------------------------------------------
from src.models.moderation import ProductBlockingReason, ProductModeration

SOFT_REASON_ID = "00000000-0001-0001-0001-000000000003"
HARD_REASON_ID = "00000000-0001-0001-0001-000000000001"


@pytest.fixture
def seeded_reasons(db):
    db.add(ProductBlockingReason(id=SOFT_REASON_ID, title="Некорректное описание", hard_block=False))
    db.add(ProductBlockingReason(id=HARD_REASON_ID, title="Запрещённый товар", hard_block=True))
    db.commit()


def make_pending_card(db, product_id=None, seller_id=None, moderator_id=None, json_before=None):
    pid = product_id or str(uuid.uuid4())
    card = ProductModeration(
        product_id=pid,
        seller_id=seller_id or str(uuid.uuid4()),
        status="PENDING",
        queue_priority=1,
        json_before=json_before,
        json_after={"name": "Test product", "skus": [{"id": "sku-1", "active_quantity": 5}]},
        moderator_id=moderator_id,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card
