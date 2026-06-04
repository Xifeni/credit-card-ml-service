import json
import logging
import os
import sys
from datetime import datetime, timezone


def setup_logging():
  level = os.getenv("LOG_LEVEL", "INFO").upper()
  logging.basicConfig(
    level=getattr(logging, level, logging.INFO),
    stream=sys.stdout,
    format="%(message)s",
  )


def log_api_event(event: str, **fields):
  payload = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "event": event,
    "service": "credit-card-ml",
    **fields,
  }
  logging.getLogger("api").info(json.dumps(payload, ensure_ascii=False))
