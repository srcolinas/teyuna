import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import fastapi.testclient as testclient
import pytest

from src import main, settings


@pytest.fixture
def static_dir(tmp_path: Path) -> Path:
    (tmp_path / "index.html").write_text(
        "<!doctype html><title>Teyuna</title>", encoding="utf-8"
    )
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('ok')\n", encoding="utf-8")
    (tmp_path / "logo.png").write_bytes(b"\x89PNG")
    return tmp_path


@pytest.fixture
def client(static_dir: Path) -> Generator[testclient.TestClient, Any, None]:
    previous = os.environ.get("TEYUNA_STATIC_DIR")
    os.environ["TEYUNA_STATIC_DIR"] = str(static_dir)
    settings.settings.cache_clear()
    app = main.create_app()
    with testclient.TestClient(app) as client_:
        yield client_
    if previous is None:
        os.environ.pop("TEYUNA_STATIC_DIR", None)
    else:
        os.environ["TEYUNA_STATIC_DIR"] = previous
    settings.settings.cache_clear()


def test_serves_index(client: testclient.TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Teyuna" in response.text


def test_spa_fallback_for_unknown_paths(client: testclient.TestClient) -> None:
    response = client.get("/?gameId=abc")
    assert response.status_code == 200
    assert "Teyuna" in response.text


def test_serves_hashed_assets(client: testclient.TestClient) -> None:
    response = client.get("/assets/app.js")
    assert response.status_code == 200
    assert "console.log" in response.text


def test_serves_root_static_files(client: testclient.TestClient) -> None:
    response = client.get("/logo.png")
    assert response.status_code == 200
    assert response.content.startswith(b"\x89PNG")


def test_health_is_unchanged(client: testclient.TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_games_api_is_unchanged(client: testclient.TestClient) -> None:
    response = client.post("/games", json={"num_players": 3})
    assert response.status_code == 201
    assert "id" in response.json()


def test_openapi_docs_still_served(client: testclient.TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200
