"""Local classroom diagnostics; may contain user-entered calculation data. stderr preserves MCP stdio protocol output."""
import os
import sys
from contextvars import ContextVar

request_id = ContextVar("request_id", default="-")

def trace(layer, event, **fields):
    if os.getenv("TRACE_DATA_FLOW") == "1" or os.getenv("APP_ENV") == "development":
        print(f"[{layer}] [{request_id.get()}] {event} {fields!r}", file=sys.stderr, flush=True)
