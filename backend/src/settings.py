from typing import Literal

import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    # NOTE: use secrets for potentially sensible data
    environment: Literal["production", "development", "staging", "local"] = "local"

    loglevel: Literal["DEBUG", "INFO", "WARNING", "ERRROR", "CRITICAL"] = "INFO"

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env", env_prefix="TEYUNA_"
    )
