"""Phase-4 E0 Chrono vehicle-spread expressibility audit.

This is a zero-training audit. It freezes the vehicle-spread axes that the
current Chrono worker can actually express before any E1 pricing panel is
registered.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/chrono_spread_expressibility_audit.py --write-prereg
    PYTHONPATH=src python scripts/feasibility_audit/chrono_spread_expressibility_audit.py --quick
    PYTHONPATH=src python scripts/feasibility_audit/chrono_spread_expressibility_audit.py --run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json  # noqa: E402
from autodrift.chrono_vehicle_backend import (  # noqa: E402
    BACKEND_ID,
    CHRONO_VEHICLE_VARIANTS,
    DEFAULT_CHRONO_VEHICLE_VARIANT,
    KNOWN_DIFFERENCES,
    smoke_scenario,
)
from autodrift.high_fidelity_interface import P0_OBSERVATION_DIM  # noqa: E402
from chrono_worker_client import ChronoWorkerClient, ChronoWorkerError  # noqa: E402


MILESTONE_ID = "m3248-phase4-e0-chrono-spread-expressibility-audit"
PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "chrono_spread_expressibility_prereg.json"
QUICK_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "chrono_spread_expressibility_quick.json"
RESULTS_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "chrono_spread_expressibility_audit.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "chrono_spread_expressibility"
FULL_ROWS_CSV = RUN_DIR / "variant_reset_rows.csv"
QUICK_ROWS_CSV = RUN_DIR / "variant_reset_rows_quick.csv"
METRICS_CSV = RUN_DIR / "metrics.csv"
QUICK_METRICS_CSV = RUN_DIR / "metrics_quick.csv"
STDERR_LOG = RUN_DIR / "chrono_worker_stderr.log"
DOC_PATH = REPO_ROOT / "docs" / "m3248-phase4-e0-chrono-spread-expressibility-audit.md"

FULL_VARIANTS = ("sedan_tmeasy", "bmw_e90_tmeasy", "uazbus_tmeasy")
QUICK_VARIANTS = ("sedan_tmeasy", "bmw_e90_tmeasy")
VARIANT_TARGET_MASS_KG = {
    "sedan_tmeasy": 1450.0,
    "bmw_e90_tmeasy": 1800.0,
    "uazbus_tmeasy": 2858.0,
}

CLAIM_BOUNDARY = (
    "Phase-4 E0 Chrono expressibility audit only: freezes the vehicle-spread "
    "axes currently expressible by the Chrono worker/backend and declares the "
    "spread envelope that E1 may price. It is zero training and does not make "
    "a driver-performance, high-fidelity sufficiency, validation ranking, "
    "promotion, repair-success, feasibility-proof, robustness, paper, or "
    "self-ID claim."
)


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


def _axis_hash(axis_table: list[dict[str, Any]]) -> str:
    payload = json.dumps(_jsonable(axis_table), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _artifact_presence() -> dict[str, bool]:
    paths = [
        "experiments/feasibility_audit/s4_hf_lite_backend_inventory.json",
        "experiments/feasibility_audit/s4_hf_lite_variant_selector_smoke.json",
        "experiments/feasibility_audit/s4_hf_lite_chrono_pricing.json",
        "experiments/feasibility_audit/chrono_native_oracle_pricing.json",
        "docs/m3218-s4-hf-lite-backend-inventory-preflight.md",
        "docs/m3219-s4-hf-lite-chrono-variant-selector-smoke.md",
        "docs/m3227-d1-s4-hf-lite-chrono-pricing.md",
        "docs/m3231-d1b-chrono-native-oracle-pricing-full.md",
        "src/autodrift/chrono_vehicle_backend.py",
    ]
    return {path: (REPO_ROOT / path).exists() for path in paths}


def build_axis_table(variants: tuple[str, ...] = FULL_VARIANTS) -> list[dict[str, Any]]:
    """Return the frozen E0 spread-axis table without running Chrono."""

    variant_values = [
        {
            "variant_id": variant_id,
            "constructor_name": CHRONO_VEHICLE_VARIANTS[variant_id].constructor_name,
            "tire_model": CHRONO_VEHICLE_VARIANTS[variant_id].tire_model,
            "target_mass_kg": VARIANT_TARGET_MASS_KG.get(variant_id),
        }
        for variant_id in variants
    ]
    return [
        {
            "axis": "vehicle_model_fixture",
            "control_class": "discrete_reset_time_selector",
            "current_status": "admitted_for_e1_primary_population_axis",
            "mechanism": "scenario['chrono_vehicle_variant'] selects a whitelisted Chrono wrapper at reset",
            "values": variant_values,
            "e1_use": "Use as the primary E1 vehicle-class spread axis crossed with frozen T-limit cells.",
            "evidence": [
                "M3219 reset/step selector smoke",
                "CHRONO_VEHICLE_VARIANTS in src/autodrift/chrono_vehicle_backend.py",
            ],
            "forbidden_interpretation": "Do not treat this as a continuous passenger-fleet coverage proof.",
        },
        {
            "axis": "wheelbase_and_track",
            "control_class": "discrete_variant_fixture",
            "current_status": "admitted_for_e1_variant_metadata",
            "mechanism": "Chrono backend_info reports wheelbase and wheeltrack from the selected wrapper",
            "values": "measured at reset in variant_reset_rows.csv",
            "e1_use": "Use for stratification and mechanism interpretation, not as an independently swept axis.",
            "evidence": ["backend_info.chrono_wheelbase_m", "backend_info.chrono_wheeltrack_m"],
            "forbidden_interpretation": "Do not infer continuous lf/lr mapping from wheelbase metadata.",
        },
        {
            "axis": "target_total_mass",
            "control_class": "continuous_reset_time_partial",
            "current_status": "admitted_with_limits",
            "mechanism": "scenario params.mass is matched by overriding Chrono chassis mass",
            "values": "continuous target total mass; E0 probes one target mass per selected variant",
            "e1_use": (
                "May be used as a total-mass stress within a selected fixture if preregistered; "
                "E1 must keep it separate from payload-position or CG-height claims."
            ),
            "evidence": ["ChronoVehicleBackend._build_and_handoff mass override", "M3219 mass-match smoke"],
            "forbidden_interpretation": "This does not move CG height, axle split, inertia, or payload position.",
        },
        {
            "axis": "payload_position_or_cg_height",
            "control_class": "not_exposed_by_current_backend",
            "current_status": "blocked_requires_connector",
            "mechanism": "no scenario key currently sets chassis CG height or payload position",
            "values": [],
            "e1_use": "Not allowed as an independent E1 axis until a backend connector exposes it and is smoked.",
            "evidence": ["KNOWN_DIFFERENCES: CG height/shift and axle split remain selected Chrono vehicle fixture"],
            "forbidden_interpretation": "Do not claim payload-position or SUV load-transfer coverage from mass override alone.",
        },
        {
            "axis": "load_transfer",
            "control_class": "emergent_chrono_fixture_not_direct_axis",
            "current_status": "admitted_as_fixture_physics_with_limits",
            "mechanism": (
                "Chrono multibody vehicle dynamics include normal-load transfer inside each selected fixture, "
                "but E0 cannot independently sweep h_cg or axle load split."
            ),
            "values": "present through selected Chrono vehicle models; direct h_cg control unavailable",
            "e1_use": "E1 may say it prices the selected Chrono fixtures with load-transfer physics active.",
            "evidence": ["Chrono::Vehicle backend", "selected vehicle wrapper reset smoke"],
            "forbidden_interpretation": "Do not claim a load-transfer parameter sweep or payload-height experiment.",
        },
        {
            "axis": "tire_parameter_set",
            "control_class": "discrete_variant_bound_fixture",
            "current_status": "admitted_with_limits",
            "mechanism": "all whitelisted variants use TMeasy, with tire fixtures bound to the vehicle wrapper",
            "values": [
                {
                    "variant_id": variant_id,
                    "tire_model": CHRONO_VEHICLE_VARIANTS[variant_id].tire_model,
                }
                for variant_id in variants
            ],
            "e1_use": (
                "May be interpreted only as vehicle-bound TMeasy fixture variation; "
                "not as an independent tire-set sweep."
            ),
            "evidence": ["CHRONO_VEHICLE_VARIANTS tire_model field", "backend_info.chrono_tire_model"],
            "forbidden_interpretation": "Do not claim winter/summer, Fiala, Pacejka, or continuous cf/cr tire coverage.",
        },
        {
            "axis": "tire_model_family",
            "control_class": "not_exposed_by_current_selector",
            "current_status": "blocked_requires_connector",
            "mechanism": "whitelisted backend selector fixes tire_model='TMEASY' for every variant",
            "values": ["TMEASY"],
            "e1_use": "Not allowed as an E1 factor without a new selector and reset/step smoke.",
            "evidence": ["CHRONO_VEHICLE_VARIANTS", "M3219"],
            "forbidden_interpretation": "Do not treat Chrono resource availability as wired tire-family control.",
        },
        {
            "axis": "continuous_lf_lr_iz_cf_cr",
            "control_class": "not_mapped_from_scenario_params",
            "current_status": "blocked_requires_connector",
            "mechanism": "scenario carries lf/lr/iz/cf/cr for provenance but backend leaves fixture geometry/inertia/tires unchanged",
            "values": [],
            "e1_use": "Not allowed as independent E1 axes under the current backend.",
            "evidence": ["M3218 mapping table", "KNOWN_DIFFERENCES"],
            "forbidden_interpretation": "Do not reuse current-sim S4L cg/Iz labels as if Chrono maps them continuously.",
        },
        {
            "axis": "drive_brake_authority",
            "control_class": "control_layer_partial",
            "current_status": "context_only_for_e1",
            "mechanism": "drive/brake scales multiply normalized inputs and clip at 1.0",
            "values": "available through scenario max_drive_force/max_brake_force but saturating above nominal",
            "e1_use": "Context/control-arm metadata only unless E1 preregisters it as a separate actuator axis.",
            "evidence": ["KNOWN_DIFFERENCES", "ChronoVehicleBackend.step input mapping"],
            "forbidden_interpretation": "Do not treat clipped command scaling as physical brake-system redesign.",
        },
        {
            "axis": "actuator_lag_and_steer_rate",
            "control_class": "mapped_control_layer",
            "current_status": "context_only_for_e1",
            "mechanism": "AutoDrift first-order/rate actuator filter is applied before Chrono driver inputs",
            "values": "scenario steer_tau, drive_tau, max_steer_rate",
            "e1_use": "May remain fixed from source rows; separate actuator-spread pricing requires its own preregistration.",
            "evidence": ["ChronoVehicleBackend._update_actuators"],
            "forbidden_interpretation": "Do not merge actuator-lag effects into vehicle-class spread without labeling.",
        },
        {
            "axis": "surface_mu",
            "control_class": "mapped_surface_axis",
            "current_status": "not_vehicle_spread_but_available",
            "mechanism": "scenario mu maps to Chrono FlatTerrain friction; friction step maps terrain mu replacement",
            "values": "continuous scalar mu",
            "e1_use": "Use only as the frozen T-limit surface/context axis, not as a vehicle-spread axis.",
            "evidence": ["M3218 mapping table", "ChronoVehicleBackend._maybe_apply_friction_step"],
            "forbidden_interpretation": "Do not call scalar mu a tire-curve shape or split-mu contact model.",
        },
        {
            "axis": "split_mu_or_per_wheel_contact_surface",
            "control_class": "not_exposed_in_executable_env_path",
            "current_status": "blocked_requires_backend_connector",
            "mechanism": "current executable path exposes one FlatTerrain scalar friction coefficient",
            "values": [],
            "e1_use": "Not allowed for E1 unless a per-wheel/per-side terrain connector is added and smoked.",
            "evidence": ["M3225 split-mu expressibility note", "ChronoVehicleBackend terrain construction"],
            "forbidden_interpretation": "Do not claim ESC split-mu coverage from scalar FlatTerrain mu.",
        },
    ]


def build_preregistration() -> dict[str, Any]:
    axis_table = build_axis_table(FULL_VARIANTS)
    return {
        "protocol": "phase4_e0_chrono_spread_expressibility_preregistration",
        "milestone": MILESTONE_ID,
        "roadmap_unit": "Phase-4 E0 Expressibility audit",
        "frozen_at_utc": utc_timestamp(),
        "frozen_before_any_e0_run": True,
        "claim_boundary": CLAIM_BOUNDARY,
        "backend_id": BACKEND_ID,
        "default_variant": DEFAULT_CHRONO_VEHICLE_VARIANT,
        "full_variants": list(FULL_VARIANTS),
        "quick_variants": list(QUICK_VARIANTS),
        "variant_target_mass_kg": VARIANT_TARGET_MASS_KG,
        "source_artifacts": _artifact_presence(),
        "frozen_axis_table_sha256": _axis_hash(axis_table),
        "acceptance_criteria": [
            "preregistration exists before full E0 run",
            "axis table schema includes axis/control_class/current_status/mechanism/e1_use/evidence/forbidden_interpretation",
            "full mode reset/steps all full_variants through the Chrono worker with finite obs72",
            "backend_info selected variant matches every requested variant",
            "at least one admitted_for_e1 primary vehicle-class axis is present",
            "payload_position_or_cg_height is explicitly blocked rather than silently aliased to mass",
            "E1 allowed and forbidden spread envelopes are written into the JSON and Markdown artifacts",
        ],
        "decision_rule": (
            "PASS iff all full_variants reset/step with finite obs72 and variant match, "
            "the frozen axis table has the required rows, and E1 has a declared vehicle-class "
            "spread envelope plus explicit blocked axes."
        ),
    }


def write_preregistration() -> dict[str, Any]:
    payload = build_preregistration()
    write_json(PREREG_JSON, payload)
    return payload


def load_preregistration() -> dict[str, Any]:
    if not PREREG_JSON.exists():
        raise FileNotFoundError(f"missing preregistration {PREREG_JSON}; run --write-prereg first")
    payload = json.loads(PREREG_JSON.read_text(encoding="utf-8"))
    if not payload.get("frozen_before_any_e0_run"):
        raise ValueError(f"{PREREG_JSON} is not marked frozen_before_any_e0_run")
    return payload


def _finite_obs(obs: np.ndarray) -> bool:
    return obs.shape == (P0_OBSERVATION_DIM,) and bool(np.isfinite(obs).all())


def _probe_variants(variants: tuple[str, ...], *, steps: int, stderr_log: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    action = np.array([0.0, -1.0, -1.0], dtype=np.float32)
    client = ChronoWorkerClient(stderr_log=stderr_log)
    try:
        for index, variant_id in enumerate(variants):
            target_mass = float(VARIANT_TARGET_MASS_KG[variant_id])
            scenario = smoke_scenario(seed=324800 + index, mu=0.82, max_steps=max(steps + 4, 12))
            scenario["scenario_id"] = f"m3248-e0-{variant_id}"
            scenario["obstacle"]["enabled"] = False
            scenario["params"]["mass"] = target_mass
            scenario["chrono_vehicle_variant"] = variant_id
            row: dict[str, Any] = {
                "variant_id": variant_id,
                "target_mass_kg": target_mass,
                "seed": 324800 + index,
            }
            try:
                obs, reset_reply = client.reset(scenario, episode_id=scenario["scenario_id"], seed=324800 + index)
                info = dict(reset_reply.get("backend_info", {}))
                step_pass = True
                step_statuses: list[str] = []
                for _ in range(steps):
                    obs, terminated, truncated, status, _diagnostics = client.step(action)
                    step_statuses.append(status)
                    step_pass = step_pass and _finite_obs(obs) and not terminated and not truncated
                row.update(
                    {
                        "reset_obs_finite": _finite_obs(obs),
                        "step_pass": bool(step_pass),
                        "step_statuses": step_statuses,
                        "backend_variant": info.get("chrono_vehicle_variant"),
                        "backend_model": info.get("chrono_vehicle_model"),
                        "backend_tire_model": info.get("chrono_tire_model"),
                        "vehicle_total_mass_kg": info.get("vehicle_total_mass"),
                        "mass_abs_error_kg": abs(float(info.get("vehicle_total_mass", float("nan"))) - target_mass),
                        "wheelbase_m": info.get("chrono_wheelbase_m"),
                        "wheeltrack_m": info.get("chrono_wheeltrack_m"),
                        "max_steer_rad": info.get("chrono_max_steer_rad"),
                        "chassis_inertia_xx_kgm2": info.get("chrono_chassis_inertia_xx_kgm2"),
                    }
                )
                row["pass"] = bool(
                    row["reset_obs_finite"]
                    and row["step_pass"]
                    and row["backend_variant"] == variant_id
                    and float(row["mass_abs_error_kg"]) <= 1e-6
                )
            except (ChronoWorkerError, Exception) as exc:
                row["pass"] = False
                row["error"] = f"{type(exc).__name__}: {exc}"
            rows.append(row)
    finally:
        client.close()
    return rows


def _axis_table_schema_ok(axis_table: list[dict[str, Any]]) -> bool:
    required = {
        "axis",
        "control_class",
        "current_status",
        "mechanism",
        "e1_use",
        "evidence",
        "forbidden_interpretation",
    }
    return bool(axis_table) and all(required.issubset(row.keys()) for row in axis_table)


def evaluate_decision(axis_table: list[dict[str, Any]], variant_rows: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = {row["axis"]: row["current_status"] for row in axis_table}
    vehicle_axis_present = any(
        row["axis"] == "vehicle_model_fixture"
        and row["current_status"] == "admitted_for_e1_primary_population_axis"
        for row in axis_table
    )
    cg_blocked = statuses.get("payload_position_or_cg_height") == "blocked_requires_connector"
    all_variants_pass = bool(variant_rows) and all(bool(row.get("pass")) for row in variant_rows)
    pass_rule = bool(_axis_table_schema_ok(axis_table) and vehicle_axis_present and cg_blocked and all_variants_pass)
    return {
        "status_pass": pass_rule,
        "e0_completed": pass_rule,
        "e1_preregistration_admitted": pass_rule,
        "all_variants_pass": all_variants_pass,
        "vehicle_axis_present": vehicle_axis_present,
        "payload_position_cg_height_blocked": cg_blocked,
        "axis_table_schema_ok": _axis_table_schema_ok(axis_table),
        "verdict": "passed" if pass_rule else "failed",
        "next_admitted_step": (
            "E1 Spread-revival pricing preregistration using the frozen E0 spread envelope"
            if pass_rule
            else "repair E0 expressibility blockers before E1 preregistration"
        ),
    }


def build_e1_envelope(axis_table: list[dict[str, Any]], variant_rows: list[dict[str, Any]]) -> dict[str, Any]:
    admitted = [row for row in axis_table if str(row["current_status"]).startswith("admitted")]
    blocked = [row for row in axis_table if "blocked" in str(row["current_status"])]
    return {
        "allowed_e1_axes": [
            {
                "axis": row["axis"],
                "control_class": row["control_class"],
                "limit": row["forbidden_interpretation"],
            }
            for row in admitted
        ],
        "blocked_without_new_connector": [
            {
                "axis": row["axis"],
                "reason": row["mechanism"],
                "connector_needed": row["e1_use"],
            }
            for row in blocked
        ],
        "recommended_e1_population_panel": {
            "vehicle_variants": [row["variant_id"] for row in variant_rows if row.get("pass")],
            "surface": "T-limit rows only until E1 preregisters any additional surface axis",
            "arms": [
                "fixed reflex with one global Chrono retune (fixed*)",
                "RLS-retuned",
                "per-instance tuned",
                "per-instance Chrono-native oracle",
            ],
            "required_language": (
                "E1 prices selected Chrono vehicle fixtures with load-transfer physics active; "
                "it does not price independent payload-position, h_cg, tire-family, or continuous lf/lr/Iz/cf/cr axes."
            ),
        },
    }


def run_audit(*, quick: bool = False, steps: int = 1) -> dict[str, Any]:
    prereg = load_preregistration()
    variants = tuple(prereg["quick_variants"] if quick else prereg["full_variants"])
    run_rows_csv = QUICK_ROWS_CSV if quick else FULL_ROWS_CSV
    result_json = QUICK_JSON if quick else RESULTS_JSON
    axis_table = build_axis_table(FULL_VARIANTS)
    variant_rows = _probe_variants(variants, steps=steps, stderr_log=STDERR_LOG)
    write_csv_rows(
        run_rows_csv,
        variant_rows,
        fieldnames=[
            "variant_id",
            "target_mass_kg",
            "seed",
            "pass",
            "reset_obs_finite",
            "step_pass",
            "backend_variant",
            "backend_model",
            "backend_tire_model",
            "vehicle_total_mass_kg",
            "mass_abs_error_kg",
            "wheelbase_m",
            "wheeltrack_m",
            "max_steer_rad",
            "chassis_inertia_xx_kgm2",
            "step_statuses",
            "error",
        ],
    )
    decision = evaluate_decision(axis_table, variant_rows)
    if quick:
        decision["e0_completed"] = False
        decision["e1_preregistration_admitted"] = False
        decision["next_admitted_step"] = "run the full E0 audit through the harness"
    payload = {
        "schema_version": 1,
        "milestone": MILESTONE_ID,
        "mode": "quick" if quick else "full",
        "created_at_utc": utc_timestamp(),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": str(PREREG_JSON.relative_to(REPO_ROOT)),
        "source_artifacts": _artifact_presence(),
        "backend_id": BACKEND_ID,
        "known_differences": list(KNOWN_DIFFERENCES),
        "axis_table_sha256": _axis_hash(axis_table),
        "axis_table": axis_table,
        "variant_reset_rows_csv": str(run_rows_csv.relative_to(REPO_ROOT)),
        "variant_reset_rows": variant_rows,
        "e1_spread_envelope": build_e1_envelope(axis_table, variant_rows),
        "decision": decision,
    }
    metrics_csv = QUICK_METRICS_CSV if quick else METRICS_CSV
    write_csv_rows(
        metrics_csv,
        [
            {"metric": "status_pass", "value": 1.0 if decision["status_pass"] else 0.0},
            {"metric": "variant_pass_count", "value": sum(1 for row in variant_rows if row.get("pass"))},
            {"metric": "variant_count", "value": len(variant_rows)},
            {"metric": "vehicle_axis_present", "value": 1.0 if decision["vehicle_axis_present"] else 0.0},
            {
                "metric": "payload_position_cg_height_blocked",
                "value": 1.0 if decision["payload_position_cg_height_blocked"] else 0.0,
            },
            {"metric": "e1_preregistration_admitted", "value": 1.0 if decision["e1_preregistration_admitted"] else 0.0},
        ],
        fieldnames=["metric", "value"],
    )
    payload["metrics_csv"] = str(metrics_csv.relative_to(REPO_ROOT))
    write_json(result_json, payload)
    if not quick:
        write_markdown(DOC_PATH, payload)
    return payload


def _format_value(value: Any) -> str:
    if isinstance(value, (list, dict)):
        return "`" + json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True) + "`"
    return str(value)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    decision = payload["decision"]
    rows = payload["variant_reset_rows"]
    lines = [
        "# M3248 Phase-4 E0 Chrono Spread Expressibility Audit",
        "",
        "Status: completed. This is a zero-training Phase-4 E0 audit; it freezes",
        "the Chrono vehicle-spread envelope that E1 is allowed to price.",
        "",
        "## Verdict",
        "",
        f"- E0 pass: **{str(decision['status_pass']).lower()}**.",
        f"- E1 preregistration admitted: **{str(decision['e1_preregistration_admitted']).lower()}**.",
        f"- Next admitted step: {decision['next_admitted_step']}.",
        f"- Frozen axis-table SHA256: `{payload['axis_table_sha256']}`.",
        "",
        "## Measured",
        "",
        "The full E0 worker probe reset and stepped the selected Chrono variants",
        "through finite obs72/action3 using one no-op control step per variant.",
        "",
        "| variant | model | tire | target mass kg | total mass kg | wheelbase m | wheeltrack m | result |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('variant_id')}`",
                    str(row.get("backend_model", "")),
                    str(row.get("backend_tire_model", "")),
                    f"{float(row.get('target_mass_kg', 0.0)):.1f}",
                    f"{float(row.get('vehicle_total_mass_kg', 0.0)):.1f}",
                    "" if row.get("wheelbase_m") is None else f"{float(row['wheelbase_m']):.3f}",
                    _format_value(row.get("wheeltrack_m", "")),
                    "pass" if row.get("pass") else "fail",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Frozen Axis Table",
            "",
            "| axis | control class | E1 status | mechanism | E1 use |",
            "|---|---|---|---|---|",
        ]
    )
    for row in payload["axis_table"]:
        lines.append(
            f"| `{row['axis']}` | `{row['control_class']}` | `{row['current_status']}` | "
            f"{row['mechanism']} | {row['e1_use']} |"
        )
    envelope = payload["e1_spread_envelope"]
    lines.extend(
        [
            "",
            "## Inferred",
            "",
            "E1 may price selected Chrono vehicle fixtures with load-transfer physics",
            "active. It may not claim an independent payload-position, h_cg,",
            "tire-family, split-mu, or continuous lf/lr/Iz/cf/cr sweep without a",
            "new connector and reset/step smoke.",
            "",
            "Recommended E1 population panel:",
            "",
            f"- Vehicle variants: {', '.join('`' + item + '`' for item in envelope['recommended_e1_population_panel']['vehicle_variants'])}.",
            f"- Surface: {envelope['recommended_e1_population_panel']['surface']}.",
            "- Arms: fixed* / RLS-retuned / per-instance tuned / per-instance Chrono-native oracle.",
            f"- Required language: {envelope['recommended_e1_population_panel']['required_language']}",
            "",
            "Blocked without a new connector:",
            "",
        ]
    )
    for row in envelope["blocked_without_new_connector"]:
        lines.append(f"- `{row['axis']}`: {row['connector_needed']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            CLAIM_BOUNDARY,
            "",
            "## Artifacts",
            "",
            f"- Preregistration: `{PREREG_JSON.relative_to(REPO_ROOT)}`",
            f"- Full JSON: `{RESULTS_JSON.relative_to(REPO_ROOT)}`",
            f"- Variant rows: `{FULL_ROWS_CSV.relative_to(REPO_ROOT)}`",
            f"- Metrics: `{METRICS_CSV.relative_to(REPO_ROOT)}`",
            f"- Script: `scripts/feasibility_audit/{Path(__file__).name}`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write-prereg", action="store_true")
    group.add_argument("--quick", action="store_true")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--steps", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.steps < 1:
        raise ValueError("--steps must be positive")
    if args.write_prereg:
        payload = write_preregistration()
        print(json.dumps({"preregistration": str(PREREG_JSON), "axis_hash": payload["frozen_axis_table_sha256"]}))
        return
    payload = run_audit(quick=bool(args.quick), steps=int(args.steps))
    print(json.dumps(payload["decision"], ensure_ascii=False, sort_keys=True))
    if not payload["decision"]["status_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
