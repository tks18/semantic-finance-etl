import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_dir: str | None = None) -> None:
    root_logger = logging.getLogger("semantic_finance_etl")
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(level)
    root_logger.propagate = False
    
    # Close and remove existing handlers to release file locks on Windows
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
        
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s"
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path / "etl.log", encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
