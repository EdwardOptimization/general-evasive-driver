"""Reset/step smoke for the S4-HF-lite Chrono vehicle-variant selector.

This is still infrastructure, not S4 pricing.  It verifies that the JSONL
Chrono worker can reset and step the default Sedan backend plus two explicit
vehicle variants through the same obs72/action3 contract.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from chrono_worker_client import ChronoWorkerClient, ChronoWorkerError  # noqa: E402
from autodrift.chrono_vehicle_backend import (  # noqa: E402
    CHRONO_VEHICLE_VARIANTS,
    DEFAULT_CHRONO_VEHICLE_VARIANT,
    smoke_scenario,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM  # noqa: E402

OUTPUT_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "s4_hf_lite_variant_selector_smoke.json"
STDERR_LOG = REPO_ROOT / "runs" / "feasibility_audit" / "s4_hf_lite_variant_selector_worker_stderr.log"

SMOKE_CASES = [
    {
        "case_id": "default_no_selector_sedan",
        "scenario_variant": None,
        "expected_variant": DEFAULT_CHRONO_VEHICLE_VARIANT,
        "target_mass": 1450.0,
        "seed": 93210,
    },
    {
        "case_id": "explicit_bmw_e90",
        "scenario_variant": "bmw_e90_tmeasy",
        "expected_variant": "bmw_e90_tmeasy",
        "target_mass": 1800.0,
        "seed": 93211,
    },
    {
        "case_id": "explicit_uazbus",
        "scenario_variant": "uazbus_tmeasy",
        "expected_variant": "uazbus_tmeasy",
        "target_mass": 2858.0,
        "seed": 93212,
    },
]


def _finite_vector(values: np.ndarray) -> bool:
    return values.shape == (P0_OBSERVATION_DIM,) and bool(np.isfinite(values).all())


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else repr(number)
    if isinstance(value, (np.integer,)):
        return int(value)
    return value


def _scenario_for_case(case: dict[str, Any], *, steps: int) -> dict[str, Any]:
    scenario = smoke_scenario(int(case["seed"]), 0.8, max_steps=max(steps + 4, 12))
    scenario["scenario_id"] = f"m3219-{case['case_id']}"
    scenario["obstacle"]["enabled"] = False
    scenario["params"]["mass"] = float(case["target_mass"])
    variant = case.get("scenario_variant")
    if variant is not None:
        scenario["chrono_vehicle_variant"] = str(variant)
    return scenario


def run_smoke(*, steps: int, stderr_log: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    client = ChronoWorkerClient(stderr_log=stderr_log)
    action = np.array([0.0, -1.0, -1.0], dtype=np.float32)
    try:
        for case in SMOKE_CASES:
            scenario = _scenario_for_case(case, steps=steps)
            row: dict[str, Any] = {
                "case_id": case["case_id"],
                "scenario_variant": case.get("scenario_variant"),
                "expected_variant": case["expected_variant"],
                "target_mass": float(case["target_mass"]),
                "seed": int(case["seed"]),
            }
            try:
                obs, reset_reply = client.reset(scenario, episode_id=str(case["case_id"]), seed=int(case["seed"]))
                backend_info = dict(reset_reply.get("backend_info", {}))
                row["reset_obs_shape"] = list(obs.shape)
                row["reset_obs_finite"] = _finite_vector(obs)
                row["backend_info"] = {
                    key: backend_info.get(key)
                    for key in [
                        "backend_id",
                        "chrono_vehicle_variant",
                        "chrono_vehicle_model",
                        "chrono_tire_model",
                        "vehicle_total_mass",
                        "target_mass",
                        "chrono_base_vehicle_mass",
                        "chrono_max_steer_rad",
                        "chrono_wheelbase_m",
                        "chrono_wheeltrack_m",
                        "chrono_chassis_inertia_xx_kgm2",
                    ]
                }
                step_rows = []
                terminated_or_truncated = False
                for step_index in range(steps):
                    obs, terminated, truncated, status, info = client.step(action)
                    terminated_or_truncated = terminated_or_truncated or terminated or truncated
                    step_rows.append(
                        {
                            "step": step_index + 1,
                            "obs_shape": list(obs.shape),
                            "obs_finite": _finite_vector(obs),
                            "terminated": bool(terminated),
                            "truncated": bool(truncated),
                            "status": status,
                            "speed": info.get("speed"),
                            "lateral_error": info.get("lateral_error"),
                        }
                    )
                row["step_rows"] = step_rows
                row["variant_match"] = backend_info.get("chrono_vehicle_variant") == case["expected_variant"]
                row["model_present"] = bool(backend_info.get("chrono_vehicle_model"))
                row["mass_match_abs_error"] = abs(
                    float(backend_info.get("vehicle_total_mass", float("nan"))) - float(case["target_mass"])
                )
                row["pass"] = bool(
                    row["reset_obs_finite"]
                    and row["variant_match"]
                    and row["model_present"]
                    and row["mass_match_abs_error"] <= 1e-6
                    and len(step_rows) == steps
                    and all(item["obs_finite"] for item in step_rows)
                    and not terminated_or_truncated
                )
            except (ChronoWorkerError, Exception) as exc:
                row["pass"] = False
                row["error"] = f"{type(exc).__name__}: {exc}"
            rows.append(row)
    finally:
        client.close()

    default_rows = [row for row in rows if row["case_id"] == "default_no_selector_sedan"]
    explicit_rows = [row for row in rows if row["case_id"] != "default_no_selector_sedan"]
    status_pass = bool(rows) and all(bool(row.get("pass")) for row in rows)
    return {
        "schema_version": 1,
        "milestone": "m3219-s4-hf-lite-chrono-variant-selector-smoke",
        "claim_boundary": {
            "allowed": [
                "Chrono vehicle variant selector reset/step smoke",
                "obs72/action3 contract preservation through the worker protocol",
                "admission of S4-HF-lite pricing pre-registration if all smoke cases pass",
            ],
            "forbidden": [
                "driver performance",
                "S4/C5 pricing result",
                "RL evidence",
                "high-fidelity sufficiency",
                "validation ranking or promotion",
                "paper evidence",
            ],
        },
        "variant_catalog": {
            key: {
                "constructor_name": value.constructor_name,
                "tire_model": value.tire_model,
                "init_chassis_z": value.init_chassis_z,
                "description": value.description,
            }
            for key, value in sorted(CHRONO_VEHICLE_VARIANTS.items())
        },
        "smoke_steps_per_case": int(steps),
        "action": action.tolist(),
        "status_pass": status_pass,
        "default_selector_preserved": bool(default_rows and default_rows[0].get("variant_match")),
        "explicit_variants_passed": bool(explicit_rows) and all(bool(row.get("pass")) for row in explicit_rows),
        "cases": rows,
        "decision": {
            "variant_selector_smoke_passed": status_pass,
            "s4_hf_lite_pricing_preregistration_admitted": status_pass,
            "s4_hf_lite_pricing_run_admitted": False,
            "next_admitted_step": (
                "write a frozen S4-HF-lite pricing pre-registration"
                if status_pass
                else "repair the Chrono variant selector before S4-HF-lite pricing pre-registration"
            ),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_JSON)
    parser.add_argument("--stderr-log", type=Path, default=STDERR_LOG)
    parser.add_argument("--steps", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.steps < 1:
        raise ValueError("--steps must be positive")
    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    stderr_log = args.stderr_log if args.stderr_log.is_absolute() else REPO_ROOT / args.stderr_log
    output.parent.mkdir(parents=True, exist_ok=True)
    stderr_log.parent.mkdir(parents=True, exist_ok=True)
    summary = run_smoke(steps=int(args.steps), stderr_log=stderr_log)
    output.write_text(json.dumps(_jsonable(summary), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary["decision"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
