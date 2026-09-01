from collections.abc import Generator
from typing import Any

import pytest

from src import settings


@pytest.fixture(autouse=True)
def require_static_dir(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> Generator[None, Any, None]:
    monkeypatch.setenv("TEYUNA_STATIC_DIR", str(tmp_path_factory.mktemp("static")))
    settings.settings.cache_clear()
    yield
    settings.settings.cache_clear()
