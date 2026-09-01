import asyncio
import contextlib
import logging
import pathlib
import random
from collections.abc import AsyncIterator, Callable
from typing import TypeVar
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


from . import game, settings
from .game import services

T = TypeVar("T")


def create_app() -> fastapi.FastAPI:
    settings_ = settings.get_settings()

    @contextlib.asynccontextmanager
    async def lifespan(app: fastapi.FastAPI) -> AsyncIterator[None]:
        poller = asyncio.create_task(
            _timeout_poller(
                app,
                poll_interval=settings_.timeout_poll_interval.total_seconds(),
            )
        )
        try:
            yield
        finally:
            poller.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await poller

    app = fastapi.FastAPI(
        title="Teyuna",
        description=(
            "Multiplayer board game HTTP API. Join with POST /games/{id}/players "
            "(Bearer token in the response), poll GET /games/{id} for `phase` and "
            "`turn_order`, then POST /games/{id}/actions with a phase-legal `kind`. "
            "Wrong-phase or illegal moves return HTTP 400. "
            "Agent playbook: docs/agents.md; rules: docs/rulebook.md."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    loglevel = logging.getLevelNamesMapping()[settings_.loglevel]
    print(f"Setting log level to: {settings_.loglevel} ({loglevel})")
    logging.basicConfig(level=loglevel)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(game.routes.router)
    _mount_observer(app, settings_.static_dir)

    return app


async def _timeout_poller(app: fastapi.FastAPI, *, poll_interval: float) -> None:
    rng = random.Random()
    while True:
        await asyncio.sleep(poll_interval)
        await _apply_due_timeouts(app=app, rng=rng)


# TODO: handling dependency overrides should be done by the fastapi framework,
# we need to investigate how to allow to access to the dependencies when they
# have been already used by the lifespan to run background tasks.
def _resolve(app: fastapi.FastAPI, dependency: Callable[[], T]) -> T:
    override = app.dependency_overrides.get(dependency)
    if override is None:
        return dependency()
    return override()


async def _apply_due_timeouts(*, app: fastapi.FastAPI, rng: random.Random) -> None:
    repository = _resolve(app, game.dependencies.get_repository)
    registry = _resolve(app, game.dependencies.get_actions_registry)
    game_locks = _resolve(app, game.dependencies.get_game_locks)
    broker = _resolve(app, game.dependencies.get_event_broker)
    for game_id, _ in repository.items():
        await services.apply_timeout_if_due(
            game_id,
            repository=repository,
            registry=registry,
            game_locks=game_locks,
            broker=broker,
            rng=rng,
        )


def _mount_observer(app: fastapi.FastAPI, static_dir: pathlib.Path) -> None:
    index = static_dir / "index.html"
    if not index.is_file():
        return

    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def observer(full_path: str) -> FileResponse:
        if full_path:
            candidate = (static_dir / full_path).resolve()
            try:
                candidate.relative_to(static_dir.resolve())
            except ValueError:
                return FileResponse(index)
            if candidate.is_file():
                return FileResponse(candidate)
        return FileResponse(index)
