import logging
import sys


def configure_logging() -> None:
    """Configure stdout logging format with timestamp and severity levels."""
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        handlers=[logging.StreamHandler(sys.stdout)],
    )