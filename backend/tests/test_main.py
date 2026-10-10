"""Application factory, error handler and sweeper tests."""

import asyncio
import sys
import types
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, field_validator

from app import main
from app.config import get_settings

SWEEP_MODULE = "app.services.submission_service"


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "healthy"}


def test_docs_enabled_in_dev() -> None:
    assert TestClient(main.create_app()).get("/openapi.json").status_code == 200


def test_docs_disabled_in_production() -> None:
    prod = get_settings().model_copy(update={"ENVIRONMENT": "production"})
    with patch.object(main, "settings", prod):
        c = TestClient(main.create_app())
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert c.get(path).status_code == 404


def test_validation_error_hides_input_and_ctx() -> None:
    class Body(BaseModel):
        password: str

        @field_validator("password")
        @classmethod
        def check(cls, v: str) -> str:
            raise ValueError("bad")

    app: FastAPI = main.create_app()

    @app.post("/_t")
    def _t(body: Body) -> None:  # pragma: no cover - never reached
        return None

    r = TestClient(app).post("/_t", json={"password": "hunter2-secret"})
    assert r.status_code == 422
    assert "hunter2-secret" not in r.text
    for err in r.json()["detail"]:
        assert "input" not in err and "ctx" not in err


def test_cors_restricted() -> None:
    r = TestClient(main.create_app()).options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert "PATCH" not in r.headers.get("access-control-allow-methods", "")


def test_run_sweeper_calls_function() -> None:
    fake = types.ModuleType(SWEEP_MODULE)
    fake.sweep_stale_submissions = MagicMock(return_value=3)  # type: ignore[attr-defined]
    with patch.dict(sys.modules, {SWEEP_MODULE: fake}):
        assert main.run_sweeper() == 3


def test_run_sweeper_tolerates_missing_function() -> None:
    with patch.dict(sys.modules, {SWEEP_MODULE: types.ModuleType(SWEEP_MODULE)}):
        assert main.run_sweeper() == 0


def test_run_sweeper_tolerates_exception() -> None:
    fake = types.ModuleType(SWEEP_MODULE)
    fake.sweep_stale_submissions = MagicMock(side_effect=RuntimeError("x"))  # type: ignore[attr-defined]
    with patch.dict(sys.modules, {SWEEP_MODULE: fake}):
        assert main.run_sweeper() == 0


def test_sweep_loop_runs_and_cancels_cleanly() -> None:
    calls: list[int] = []

    def fake_sweep() -> int:
        calls.append(1)
        return 0

    async def runner() -> None:
        with patch.object(main, "run_sweeper", fake_sweep):
            task = asyncio.create_task(main._sweep_loop(interval=0.01))
            await asyncio.sleep(0.1)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    asyncio.run(runner())
    assert len(calls) >= 2
