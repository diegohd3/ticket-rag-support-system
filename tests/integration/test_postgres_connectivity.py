from __future__ import annotations

import os

import psycopg
import pytest


@pytest.mark.integration
def test_can_connect_to_postgres_when_enabled() -> None:
    if os.getenv("RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("Set RUN_INTEGRATION_TESTS=1 to run integration tests.")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for integration tests.")

    # SQLAlchemy URL -> psycopg URL for direct connectivity check.
    dsn = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            row = cur.fetchone()
    assert row == (1,)
