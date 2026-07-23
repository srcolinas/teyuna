"""Configure stdlib logging for simulated players."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

_FORMATTER = logging.Formatter(
    "%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def resolve_log_dir(logdir: Path | None = None) -> Path:
    """Return the log directory for this run, creating it if needed.

    If ``logdir`` is given, use it directly; otherwise ``logs/YYYY-MM-DD-HH-MM``.
    """
    if logdir is not None:
        path = logdir
    else:
        stamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
        path = Path("logs") / stamp
    path.mkdir(parents=True, exist_ok=True)
    return path


def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(logging.INFO)
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    logging.getLogger("httpcore2").setLevel(logging.WARNING)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(_FORMATTER)
    root.addHandler(stream_handler)


def ensure_file_logger(
    logger_name: str, filename: str, *, logdir: Path
) -> logging.Logger:
    """Attach a FileHandler under ``logdir`` once for ``logger_name``."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = True

    target = logdir / filename
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
    return f"teyuna_sdk.agent.{nickname}"


def ensure_agent_logger(nickname: str, *, logdir: Path) -> logging.Logger:
    return ensure_file_logger(
        agent_logger_name(nickname), f"{nickname}.log", logdir=logdir
    )


def ensure_game_loop_logger(*, logdir: Path) -> logging.Logger:
    return ensure_file_logger("teyuna_sdk.loop", "game_loop.log", logdir=logdir)
