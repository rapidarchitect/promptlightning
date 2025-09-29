from __future__ import annotations
import sqlite3, json, time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict, Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY,
  prompt_id TEXT,
  version TEXT,
  inputs_json TEXT,
  output_text TEXT,
  cost REAL,
  latency_ms INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

class Logger:
    def __init__(self, db_path: str | Path) -> None:
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as con:
            con.execute(_SCHEMA)

    def write(self, prompt_id: str, version: str, inputs: Dict[str, Any], output: str,
              cost: float | None = None, latency_ms: int | None = None) -> None:
        with sqlite3.connect(self.path) as con:
            con.execute(
                "INSERT INTO logs(prompt_id,version,inputs_json,output_text,cost,latency_ms) VALUES (?,?,?,?,?,?)",
                (prompt_id, version, json.dumps(inputs, ensure_ascii=False), output, cost, latency_ms)
            )

@contextmanager
def run(logger: Optional[Logger], prompt_id: str, version: str):
    t0 = time.time()
    record = {"inputs": None, "output": None, "cost": None, "latency_ms": None}
    try:
        yield record
    finally:
        if logger:
            latency = int((time.time() - t0) * 1000)
            logger.write(prompt_id, version, record["inputs"] or {}, record["output"] or "",
                         cost=record["cost"], latency_ms=record["latency_ms"] or latency)