"""Configure stdlib logging for simulated players."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

_FORMATTER = logging.Formatter(
    "%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_log_dir: Path | None = None


def log_dir() -> Path:
    """Return this run's log directory (created once).

    Uses ``TEYUNA_LOG_DIR`` if set; otherwise ``TEYUNA_LOG_ROOT`` (default
    ``logs``) / ``YYYY-MM-DD-HH-MM`` so each run gets a fresh folder.
    """
    global _log_dir
    if _log_dir is not None:
        return _log_dir

    if explicit := os.environ.get("TEYUNA_LOG_DIR"):
        path = Path(explicit)
    else:
        root = Path(os.environ.get("TEYUNA_LOG_ROOT", "logs"))
        stamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
        path = root / stamp

    path.mkdir(parents=True, exist_ok=True)
    _log_dir = path
    return path


def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(_FORMATTER)
    root.addHandler(stream_handler)


def ensure_file_logger(logger_name: str, filename: str) -> logging.Logger:
    """Attach a FileHandler under this run's log dir once for ``logger_name``."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = True

    target = log_dir() / filename
    for handler in logger.handlers:
        if (
            isinstance(handler, logging.FileHandler)
            and Path(handler.baseFilename) == target.resolve()
        ):
            return logger

    file_handler = logging.FileHandler(target)
    file_handler.setFormatter(_FORMATTER)
    logger.addHandler(file_handler)
    return logger


def agent_logger_name(nickname: str) -> str:
    return f"teyuna_players.agent.{nickname}"


def ensure_agent_logger(nickname: str) -> logging.Logger:
    return ensure_file_logger(agent_logger_name(nickname), f"{nickname}.log")


def ensure_game_loop_logger() -> logging.Logger:
    return ensure_file_logger("teyuna_players.loop", "game_loop.log")
