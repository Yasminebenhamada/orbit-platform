import pytest
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from app.main import app
from app.dependencies import get_session, get_http_client
import app.dependencies as _deps

# ---------------------------------------------------------------------------
# In-memory SQLite engine — no real PostgreSQL needed during tests.
# ---------------------------------------------------------------------------
sqlite_url = "sqlite:///:memory:"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


def _create_tables():
    """Create all tables in the SQLite test database."""
    SQLModel.metadata.create_all(engine)


# Patch the module-level engine so the lifespan's create_db_and_tables()
# writes to SQLite instead of trying to reach PostgreSQL.
_deps.engine = engine
_create_tables()


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
      - get_session      → in-memory SQLite session
      - get_http_client  → AsyncMock (no real network calls)
    """
    mock_client, _ = mock_http_client

    # get_http_client is an async generator; the override must also be an
    # async generator so FastAPI's dependency injection handles it correctly.
    async def override_http_client():
        yield mock_client

    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_http_client] = override_http_client

    yield TestClient(app)

    app.dependency_overrides.clear()
