import json
import logging
import time
from contextvars import ContextVar
from typing import Any, Dict

correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")
task_id_ctx: ContextVar[str] = ContextVar("task_id", default="")


class JSONFormatter(logging.Formatter):
    """Formatador de logs em formato JSON estruturado contendo correlation_id e task_id."""

    def format(self, record: logging.LogRecord) -> str:
        log_object: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get(),
            "task_id": task_id_ctx.get(),
        }

        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data"):
            log_object["extra"] = getattr(record, "extra_data")

        return json.dumps(log_object, ensure_ascii=False)


def setup_logging() -> None:
    """Configura o logger raiz para padrão JSON estruturado."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
