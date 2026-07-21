import asyncio
import contextlib
import logging
import random
from collections.abc import AsyncIterator, Callable
from typing import TypeVar

import fastapi

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

    app = fastapi.FastAPI(lifespan=lifespan)

    loglevel = logging.getLevelNamesMapping()[settings_.loglevel]
    print(f"Setting log level to: {settings_.loglevel} ({loglevel})")
    logging.basicConfig(level=loglevel)

    app.include_router(game.routes.router)

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
