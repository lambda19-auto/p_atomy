import logging
from datetime import datetime
from pathlib import Path


def setup_logging(log_dir: str, app_name: str = "atomy-bot") -> None:
    target_dir = Path(log_dir)
    if not target_dir.is_absolute():
        target_dir = Path(__file__).resolve().parent.parent / target_dir

    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    all_logs_file = target_dir / f"{app_name}-all-{timestamp}.log"
    error_logs_file = target_dir / f"{app_name}-error-{timestamp}.log"

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    all_file_handler = logging.FileHandler(all_logs_file, encoding="utf-8")
    all_file_handler.setLevel(logging.INFO)
    all_file_handler.setFormatter(formatter)

    error_file_handler = logging.FileHandler(error_logs_file, encoding="utf-8")
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(all_file_handler)
    root_logger.addHandler(error_file_handler)
    root_logger.addHandler(console_handler)
