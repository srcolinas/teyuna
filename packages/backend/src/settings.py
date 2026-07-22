import datetime
import functools
from typing import Literal

import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    # NOTE: use secrets for potentially sensible data
    environment: Literal["production", "development", "staging", "local"] = "local"

    loglevel: Literal["DEBUG", "INFO", "WARNING", "ERRROR", "CRITICAL"] = "INFO"

    lobby_timeout: datetime.timedelta = datetime.timedelta(minutes=2)
    first_placement_timeout: datetime.timedelta = datetime.timedelta(seconds=60)
    second_placement_timeout: datetime.timedelta = datetime.timedelta(seconds=60)
    dice_roll_timeout: datetime.timedelta = datetime.timedelta(seconds=30)
    discard_resources_timeout: datetime.timedelta = datetime.timedelta(seconds=45)
    dice_play_warrior_timeout: datetime.timedelta = datetime.timedelta(seconds=30)
    dice_play_mamo_timeout: datetime.timedelta = datetime.timedelta(seconds=30)
    dice_play_blessed_timeout: datetime.timedelta = datetime.timedelta(seconds=30)
    dice_play_pathfinder_timeout: datetime.timedelta = datetime.timedelta(seconds=30)
    move_conquistator_timeout: datetime.timedelta = datetime.timedelta(seconds=30)
    trade_and_build_timeout: datetime.timedelta = datetime.timedelta(seconds=90)
    trade_and_build_play_warrior_timeout: datetime.timedelta = datetime.timedelta(
        seconds=30
    )
    trade_and_build_play_mamo_timeout: datetime.timedelta = datetime.timedelta(
        seconds=30
    )
    trade_and_build_play_blessed_timeout: datetime.timedelta = datetime.timedelta(
        seconds=30
    )
    trade_and_build_play_pathfinder_timeout: datetime.timedelta = datetime.timedelta(
        seconds=30
    )
    timeout_poll_interval: datetime.timedelta = datetime.timedelta(seconds=1)

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env", env_prefix="TEYUNA_"
    )


@functools.cache
def settings() -> Settings:
    return Settings()


def get_settings() -> Settings:
    return settings()
