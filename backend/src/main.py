import contextlib
import logging
from collections.abc import AsyncIterator
from typing import TypedDict

import fastapi
from fastapi import status

from . import dependencies, settings
from .routes import game


def create_app(settings_: settings.Settings) -> fastapi.FastAPI:
    @contextlib.asynccontextmanager
    async def lifespan(app: fastapi.FastAPI) -> AsyncIterator[None]:
        # Add any piece of configuration require to run the system.
        # Ideally, we should include all configuration here and avoid the
        # use of global variables, but sometimes the third party libraries
        # don't really help, so we need to make exceptions.

        yield
        # Release any potential resource that was acquired while setting
        # the above configuration, like deleting temporary files or closing
        # db connections.

    app = fastapi.FastAPI(lifespan=lifespan)

    loglevel = logging.getLevelNamesMapping()[settings_.loglevel]
    print(f"Setting log level to: {settings_.loglevel} ({loglevel})")
    logging.basicConfig(level=loglevel)

    app.include_router(game.router)

    return app


app = create_app(dependencies.settings())


class _HealthResponse(TypedDict):
    message: str


@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    response_description="Health check",
)
def health_check() -> _HealthResponse:
    # NOTE: here we should implement all necessary validations,
    # like checking the database connection, the cache connection, etc.
    return {"message": "OK"}
