"""JSONL stdin/stdout worker exposing ChronoVehicleBackend to a driver process.

This process must run inside the pinned ``chrono`` conda environment
(pychrono 10.0.0). The incumbent driver cannot run there (its import chain
needs torch), so the closed-loop split is: the base-environment orchestrator
runs the deployable driver and this worker runs only the dynamics backend.

Protocol (one JSON object per line; every response line is prefixed with
``@CHRONO@`` so that any stray native-library output cannot corrupt it):

  {"cmd": "ping"}                                   -> {"ok": true, "pong": true, ...}
  {"cmd": "reset", "scenario": {...}, "episode_id"} -> {"ok": true, "obs": [72], "info": {...}}
  {"cmd": "step", "action": [s, t, b]}              -> {"ok": true, "obs": [72],
                                                        "terminated": bool, "truncated": bool,
                                                        "status": str, "info": {...}}
  {"cmd": "step_many", "actions": [[s, t, b], ...]} -> {"ok": true, "steps": [{...}, ...],
                                                        "stopped_early": bool}
  {"cmd": "close"}                                  -> {"ok": true, "closed": true} and exit

Deterministic: the backend is rebuilt from the scenario dict on every reset;
no RNG is used anywhere in this process.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO_SRC = Path(__file__).resolve().parents[2] / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

import numpy as np

from autodrift.chrono_vehicle_backend import BACKEND_ID, ChronoVehicleBackend, KNOWN_DIFFERENCES
from autodrift.high_fidelity_interface import BackendResetRequest

PREFIX = "@CHRONO@"


def _jsonable(value):
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else repr(number)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    return value


def _emit(payload: dict) -> None:
    sys.stdout.write(PREFIX + json.dumps(_jsonable(payload), separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> None:
    backend = ChronoVehicleBackend()
    _emit({"ok": True, "ready": True, "backend_id": BACKEND_ID, "known_difference_count": len(KNOWN_DIFFERENCES)})
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
            cmd = str(message.get("cmd", ""))
            if cmd == "ping":
                _emit({"ok": True, "pong": True, "backend_id": BACKEND_ID})
            elif cmd == "reset":
                result = backend.reset(
                    BackendResetRequest(
                        seed=message.get("seed"),
                        scenario_spec_id=str(message.get("episode_id", "")),
                        role_family="chrono_backend_worker",
                        options={"scenario": message["scenario"]},
                    )
                )
                obs = backend.observation(result.actor_view)
                _emit(
                    {
                        "ok": True,
                        "obs": obs.tolist(),
                        "info": result.diagnostics,
                        "backend_info": result.backend_info,
                    }
                )
            elif cmd == "step":
                result = backend.step(np.asarray(message["action"], dtype=np.float32))
                obs = backend.observation(result.actor_view)
                _emit(
                    {
                        "ok": True,
                        "obs": obs.tolist(),
                        "terminated": bool(result.terminated_by_backend),
                        "truncated": bool(result.truncated_by_backend),
                        "status": result.backend_status,
                        "info": result.diagnostics,
                    }
                )
            elif cmd == "step_many":
                rows = []
                stopped_early = False
                for action in message["actions"]:
                    result = backend.step(np.asarray(action, dtype=np.float32))
                    obs = backend.observation(result.actor_view)
                    row = {
                        "obs": obs.tolist(),
                        "terminated": bool(result.terminated_by_backend),
                        "truncated": bool(result.truncated_by_backend),
                        "status": result.backend_status,
                        "info": result.diagnostics,
                    }
                    rows.append(row)
                    if row["terminated"] or row["truncated"]:
                        stopped_early = True
                        break
                _emit({"ok": True, "steps": rows, "stopped_early": stopped_early})
            elif cmd == "close":
                backend.close()
                _emit({"ok": True, "closed": True})
                return
            else:
                _emit({"ok": False, "error": f"unknown cmd: {cmd}"})
        except Exception as exc:  # report and keep serving
            _emit({"ok": False, "error": f"{type(exc).__name__}: {exc}"})


if __name__ == "__main__":
    main()
