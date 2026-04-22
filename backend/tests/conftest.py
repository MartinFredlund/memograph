from uuid import uuid4

import pytest
from neo4j import GraphDatabase
from httpx import ASGITransport, AsyncClient
import pytest_asyncio

from testcontainers.neo4j import Neo4jContainer
from app.main import app
from app.auth.schemas import UserRole
from app.auth.service import create_access_token
from app.dependencies import get_db_session


@pytest.fixture(scope="session")
def neo4j_container():
    """
    Spin up a real Neo4j container once per test session.

    Using session scope because starting Neo4j takes ~10-15s — we don't want
    that cost per test. Tests must clean up their own data between runs
    (see the `db_session` fixture below) so session-scoped reuse is safe.
    """
    with Neo4jContainer("neo4j:5-community") as container:
        yield container


@pytest.fixture(scope="session")
def neo4j_driver(neo4j_container):
    """
    One driver per test session, connected to the test container.

    Matches production: the real app also uses one driver for its whole
    lifetime (see app/db/neo4j_driver.py). Drivers are thread-safe and
    manage their own connection pool.
    """
    driver = GraphDatabase.driver(
        neo4j_container.get_connection_url(),
        auth=("neo4j", neo4j_container.password),
    )
    yield driver
    driver.close()


@pytest.fixture
def db_session(neo4j_driver):
    """
    Fresh, empty database for every test.

    We wipe all data *before* each test (not after) so that if a test
    fails mid-way, we can still inspect the container state manually.
    Constraints are re-created each time because `DETACH DELETE` only
    removes data, not schema — but we also re-assert them in case a
    previous test dropped one.
    """
    with neo4j_driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        session.run(
            "CREATE CONSTRAINT person_uid IF NOT EXISTS "
            "FOR (p:Person) REQUIRE p.uid IS UNIQUE"
        )
        session.run(
            "CREATE CONSTRAINT user_username IF NOT EXISTS "
            "FOR (u:User) REQUIRE u.username IS UNIQUE"
        )
        session.run(
            "CREATE FULLTEXT INDEX search_index IF NOT EXISTS "
            "FOR (n:Person|Event|Place) ON EACH [n.name]"
        )
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    """
    Async HTTP client bound to the FastAPI app, with the database
    dependency overridden to use the test container session.

    Using ASGITransport (instead of a real TCP server) means requests
    go straight into the app in-process — fast, no port allocation,
    no network flakiness.
    """

    def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# Tokens are generated directly (not via the login endpoint) because
# get_current_user only decodes the JWT — it doesn't look up the user
# in the database. RBAC tests need a valid token with the right role,
# not a real user row.


@pytest.fixture
def admin_token() -> str:
    return create_access_token(str(uuid4()), UserRole.ADMIN)


@pytest.fixture
def editor_token() -> str:
    return create_access_token(str(uuid4()), UserRole.EDITOR)


@pytest.fixture
def viewer_token() -> str:
    return create_access_token(str(uuid4()), UserRole.VIEWER)
