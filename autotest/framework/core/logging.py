from __future__ import annotations

import os
from pathlib import Path

from loguru import logger


def setup_logger() -> None:
    logger.remove()
    level = os.getenv("LOG_LEVEL", "INFO").upper()

    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=level,
        colorize=True,
        backtrace=False,
        diagnose=False,
    )

    log_dir = Path(os.getenv("LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_dir / "run.log",
        level=level,
        rotation="5 MB",
        retention=5,
        encoding="utf-8",
    )

