import functools

from . import settings as settings_


@functools.cache
def settings() -> settings_.Settings:
    return settings_.Settings()
