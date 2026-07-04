import contextlib
import logging
from collections.abc import AsyncIterator

import fastapi

from . import active, proposed, settings


def create_app() -> fastapi.FastAPI:
    settings_ = settings.settings()

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

    app.include_router(proposed.router)
    app.include_router(active.router)

    return app
