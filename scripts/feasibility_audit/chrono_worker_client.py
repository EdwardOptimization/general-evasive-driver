"""Client for the chrono backend worker subprocess (JSONL over pipes).

Spawns ``chrono_backend_worker.py`` inside the pinned ``chrono`` conda env via
``conda run`` and exposes reset/step/close. Used by the base-environment
orchestrators (which run the incumbent driver) so that pychrono never has to
be importable in the base environment and torch never has to be importable in
the chrono environment.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

PREFIX = "@CHRONO@"
SCRIPTS_DIR = Path(__file__).resolve().parent
WORKER_PATH = SCRIPTS_DIR / "chrono_backend_worker.py"
DEFAULT_LAUNCH = ("conda", "run", "--no-capture-output", "-n", "chrono", "python")


class ChronoWorkerError(RuntimeError):
    pass


class ChronoWorkerClient:
    def __init__(self, *, launch: tuple[str, ...] = DEFAULT_LAUNCH, stderr_log: Path | None = None):
        self._stderr_handle = None
        stderr_target = subprocess.DEVNULL
        if stderr_log is not None:
            stderr_log.parent.mkdir(parents=True, exist_ok=True)
            self._stderr_handle = open(stderr_log, "w", encoding="utf-8")
            stderr_target = self._stderr_handle
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)  # the worker inserts the repo src path itself
        self._proc = subprocess.Popen(
            list(launch) + [str(WORKER_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr_target,
            text=True,
            bufsize=1,
            env=env,
        )
        ready = self._read()
        if not ready.get("ready"):
            raise ChronoWorkerError(f"worker did not become ready: {ready}")
        self.backend_id = str(ready.get("backend_id", ""))

    def _read(self) -> dict[str, Any]:
        while True:
            line = self._proc.stdout.readline()
            if line == "":
                raise ChronoWorkerError("worker terminated unexpectedly (EOF on stdout)")
            line = line.strip()
            if line.startswith(PREFIX):
                payload = json.loads(line[len(PREFIX):])
                if not payload.get("ok", False):
                    raise ChronoWorkerError(str(payload.get("error", "unknown worker error")))
                return payload
            # ignore stray non-protocol output from native libraries

    def _send(self, message: dict[str, Any]) -> dict[str, Any]:
        self._proc.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self._proc.stdin.flush()
        return self._read()

    def reset(self, scenario: dict[str, Any], *, episode_id: str = "", seed: int | None = None) -> tuple[np.ndarray, dict]:
        reply = self._send({"cmd": "reset", "scenario": scenario, "episode_id": episode_id, "seed": seed})
        return np.asarray(reply["obs"], dtype=np.float32), reply

    def step(self, action: np.ndarray) -> tuple[np.ndarray, bool, bool, str, dict]:
        reply = self._send({"cmd": "step", "action": np.asarray(action, dtype=float).tolist()})
        return (
            np.asarray(reply["obs"], dtype=np.float32),
            bool(reply["terminated"]),
            bool(reply["truncated"]),
            str(reply["status"]),
            dict(reply["info"]),
        )

    def close(self) -> None:
        try:
            if self._proc.poll() is None:
                self._proc.stdin.write(json.dumps({"cmd": "close"}) + "\n")
                self._proc.stdin.flush()
                self._proc.wait(timeout=30)
        except Exception:
            self._proc.kill()
        finally:
            if self._stderr_handle is not None:
                self._stderr_handle.close()
