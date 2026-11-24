import pytest
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from app.main import app
from app.dependencies import get_session, get_http_client

# ---------------------------------------------------------------------------
# In-memory SQLite engine — no real PostgreSQL needed during tests.
# ---------------------------------------------------------------------------
sqlite_url = "sqlite:///:memory:"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
SQLModel.metadata.create_all(engine)


@pytest.fixture(name="session")
def session_fixture():
    """
    Provide a database session that rolls back after every test so each
    test starts with a clean slate without recreating the schema.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(name="mock_http_client")
def mock_http_client_fixture():
    """
    Return a pre-configured AsyncMock that simulates interns-api responding
    with HTTP 200 (intern found).  Tests that need a 404 response can
    override response.status_code inside the test body.
    """
    mock_response = AsyncMock()
    mock_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    return mock_client, mock_response


@pytest.fixture(name="client")
def client_fixture(session: Session, mock_http_client):
    """
    FastAPI test client with both dependencies overridden:
      - get_session  → in-memory SQLite session
      - get_http_client → AsyncMock (no real network calls)
    """
    mock_client, _ = mock_http_client

    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_http_client] = lambda: mock_client

    yield TestClient(app)

    app.dependency_overrides.clear()
