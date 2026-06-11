"""Inventory the current Chrono backend for the S4-HF-lite pricing route.

This is a zero-rollout preflight.  It answers one narrow question:

    Can the repository's currently wired Chrono worker directly price the
    S4 lateral/tire/load-transfer population, or does the backend need a
    variant selector before any pricing run is admitted?

The script is intentionally split-process.  The base environment runs this
file; the pinned ``chrono`` conda environment is queried through
``conda run -n chrono python -`` so pychrono never has to be importable here.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = REPO_ROOT / "src" / "autodrift" / "chrono_vehicle_backend.py"
WORKER_PATH = REPO_ROOT / "scripts" / "feasibility_audit" / "chrono_backend_worker.py"

DEFAULT_OUTPUT = REPO_ROOT / "experiments" / "feasibility_audit" / "s4_hf_lite_backend_inventory.json"
DEFAULT_DOC = REPO_ROOT / "docs" / "m3218-s4-hf-lite-backend-inventory-preflight.md"

PASSENGER_LIKE_MODELS = {
    "audi",
    "bmw",
    "gclass",
    "Nissan_Patrol",
    "sedan",
    "uaz",
    "VW_microbus",
}

TARGET_WRAPPERS = [
    "Sedan",
    "BMW_E90",
    "HMMWV",
    "Gator",
    "UAZBUS",
    "CityBus",
    "FEDA",
    "ARTcar",
]

CHRONO_PROBE = r"""
import json
import os

import pychrono as chrono
import pychrono.vehicle as veh

PASSENGER_LIKE_MODELS = {
    "audi",
    "bmw",
    "gclass",
    "Nissan_Patrol",
    "sedan",
    "uaz",
    "VW_microbus",
}
TARGET_WRAPPERS = [
    "Sedan",
    "BMW_E90",
    "HMMWV",
    "Gator",
    "UAZBUS",
    "CityBus",
    "FEDA",
    "ARTcar",
]

data_path = chrono.GetChronoDataPath()
vehicle_data_path = os.path.join(data_path, "vehicle")

version_attrs = {}
for name in sorted(dir(chrono)):
    upper = name.upper()
    if "VERSION" not in upper:
        continue
    value = getattr(chrono, name)
    if callable(value):
        try:
            value = value()
        except TypeError:
            value = repr(value)
    version_attrs[name] = str(value)

vehicle_dirs = []
vehicle_json_files = []
json_by_model = {}
tire_json_by_model = {}
vehicle_json_by_model = {}

if os.path.isdir(vehicle_data_path):
    for root, dirs, files in os.walk(vehicle_data_path):
        rel = os.path.relpath(root, vehicle_data_path)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth <= 2:
            vehicle_dirs.append(rel)
        for filename in files:
            if not filename.endswith(".json"):
                continue
            rel_file = os.path.relpath(os.path.join(root, filename), vehicle_data_path)
            vehicle_json_files.append(rel_file)
            top = rel_file.split(os.sep, 1)[0]
            json_by_model[top] = json_by_model.get(top, 0) + 1
            lower = rel_file.lower()
            if "/tire/" in lower or "tire" in lower:
                tire_json_by_model.setdefault(top, []).append(rel_file)
            if "/vehicle/" in lower or lower.endswith("_vehicle.json") or lower.endswith("vehicle.json"):
                vehicle_json_by_model.setdefault(top, []).append(rel_file)
        if depth >= 4:
            dirs[:] = []

wrapper_names = sorted(name for name in dir(veh) if name and name[0].isupper() and not name.startswith("__"))
tire_model_attrs = sorted(
    name for name in dir(veh)
    if "TireModelType" in name or name in {"FialaTire", "Pac02Tire", "Pac89Tire", "RigidTire", "TMeasyTire"}
)
tire_class_attrs = sorted(name for name in dir(veh) if "Tire" in name and name and name[0].isupper())[:200]

selected_wrappers = {name: hasattr(veh, name) for name in TARGET_WRAPPERS}
candidate_models = []
for model in sorted(json_by_model):
    if model in PASSENGER_LIKE_MODELS:
        candidate_models.append(
            {
                "model": model,
                "json_count": int(json_by_model.get(model, 0)),
                "vehicle_json_sample": sorted(vehicle_json_by_model.get(model, []))[:8],
                "tire_json_sample": sorted(tire_json_by_model.get(model, []))[:12],
            }
        )

print(json.dumps(
    {
        "ok": True,
        "chrono_data_path": data_path,
        "vehicle_data_path": vehicle_data_path,
        "chrono_version_attrs": version_attrs,
        "vehicle_dir_count": len(vehicle_dirs),
        "vehicle_dirs_sample": sorted(vehicle_dirs)[:160],
        "vehicle_json_count": len(vehicle_json_files),
        "json_by_model": dict(sorted(json_by_model.items())),
        "candidate_passenger_like_models": candidate_models,
        "vehicle_module_class_count": len(wrapper_names),
        "vehicle_module_class_sample": wrapper_names[:220],
        "selected_wrapper_presence": selected_wrappers,
        "tire_model_attrs": tire_model_attrs,
        "tire_class_attrs_sample": tire_class_attrs,
    },
    ensure_ascii=False,
    sort_keys=True,
))
"""


def _repo_imports() -> tuple[str, list[str]]:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from autodrift.chrono_vehicle_backend import BACKEND_ID, KNOWN_DIFFERENCES

    return BACKEND_ID, list(KNOWN_DIFFERENCES)


def _extract_json(stdout: str) -> dict[str, Any]:
    start = stdout.find("{")
    end = stdout.rfind("}")
    if start < 0 or end < start:
        raise ValueError("chrono probe did not emit a JSON object")
    return json.loads(stdout[start : end + 1])


def _run_chrono_probe(launch: list[str], timeout_s: float) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            launch + ["-"],
            input=CHRONO_PROBE,
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            timeout=timeout_s,
            check=False,
        )
    except FileNotFoundError as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "launch": launch}
    except subprocess.TimeoutExpired as exc:
        return {"ok": False, "error": f"TimeoutExpired after {timeout_s:g}s", "launch": launch, "stdout": exc.stdout, "stderr": exc.stderr}

    if completed.returncode != 0:
        return {
            "ok": False,
            "returncode": completed.returncode,
            "launch": launch,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        }
    try:
        payload = _extract_json(completed.stdout)
    except Exception as exc:
        return {
            "ok": False,
            "returncode": completed.returncode,
            "launch": launch,
            "error": f"{type(exc).__name__}: {exc}",
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        }
    payload["launch"] = launch
    return payload


def _inspect_current_backend() -> dict[str, Any]:
    source = BACKEND_PATH.read_text(encoding="utf-8")
    worker_source = WORKER_PATH.read_text(encoding="utf-8")
    backend_id, known_differences = _repo_imports()
    has_variant_catalog = "CHRONO_VEHICLE_VARIANTS" in source
    has_variant_resolver = "_resolve_vehicle_variant" in source
    return {
        "backend_id": backend_id,
        "backend_path": str(BACKEND_PATH.relative_to(REPO_ROOT)),
        "worker_path": str(WORKER_PATH.relative_to(REPO_ROOT)),
        "hardcoded_sedan_constructor": bool(re.search(r"\bveh\.Sedan\(\)", source)),
        "hardcoded_tmeasy_tire": "SetTireType(veh.TireModelType_TMEASY)" in source,
        "worker_constructs_default_backend": "ChronoVehicleBackend()" in worker_source,
        "scenario_carries_lateral_params": all(token in source for token in ['"iz"', '"lf"', '"lr"', '"cf"', '"cr"']),
        "has_runtime_vehicle_variant_selector": bool(has_variant_catalog and has_variant_resolver),
        "known_differences": known_differences,
        "current_mapping": [
            {
                "channel": "mu",
                "status": "mapped",
                "note": "Scenario mu is mapped to Chrono FlatTerrain friction, including friction-step replacement.",
            },
            {
                "channel": "mass",
                "status": "partial",
                "note": "Total mass is matched through a chassis-mass override; CG, axle split, and inertia remain Sedan.",
            },
            {
                "channel": "drive_scale/brake_scale",
                "status": "partial",
                "note": "Mapped as throttle/brake command scaling and clipped at 1.0, so >1 scales saturate.",
            },
            {
                "channel": "drive_tau/steer_tau/max_steer_rate",
                "status": "mapped_control_layer",
                "note": "AutoDrift-style first-order/rate actuator filter is applied before Chrono driver inputs.",
            },
            {
                "channel": "lf/lr/cg_shift/axle_load_split",
                "status": "not_mapped",
                "note": "Scenario carries lf/lr but current backend leaves Sedan geometry and load split unchanged.",
            },
            {
                "channel": "iz/inertia_scale",
                "status": "not_mapped",
                "note": "Scenario carries iz but current backend does not alter Chrono inertia tensors.",
            },
            {
                "channel": "cf/cr/tire_curve_family",
                "status": "not_mapped",
                "note": "Scenario carries cf/cr but current backend does not map those stiffness scales into tire parameters.",
            },
            {
                "channel": "vehicle_model",
                "status": "mapped_selector" if has_variant_catalog and has_variant_resolver else "not_mapped",
                "note": (
                    "The backend exposes a whitelisted scenario chrono_vehicle_variant selector."
                    if has_variant_catalog and has_variant_resolver
                    else "The backend constructs veh.Sedan() unconditionally and the worker has no variant option."
                ),
            },
        ],
    }


def _build_report(chrono_probe: dict[str, Any], backend: dict[str, Any]) -> dict[str, Any]:
    chrono_resources_available = bool(chrono_probe.get("ok")) and int(chrono_probe.get("vehicle_json_count", 0)) > 0
    candidate_count = len(chrono_probe.get("candidate_passenger_like_models", [])) if chrono_probe.get("ok") else 0
    has_selector = bool(backend.get("has_runtime_vehicle_variant_selector"))
    direct_pricing = False
    extension_supported = chrono_resources_available and candidate_count >= 2
    if not has_selector:
        blocker = (
            "The repository worker/backend still hard-code veh.Sedan() with TireModelType_TMEASY and expose no variant selector; "
            "scenario lf/lr/iz/cf/cr are carried but not mapped into Chrono dynamics."
        )
        next_step = "M3219 Chrono variant-selector smoke before any S4-HF-lite pricing run"
    else:
        blocker = (
            "The repository backend now exposes a vehicle variant selector, but direct S4-HF-lite pricing still requires "
            "the reset-step smoke artifact, a frozen pricing pre-registration, and an explicit decision on the still-unmapped "
            "lf/lr/Iz/cf/cr lateral/tire channels."
        )
        next_step = "S4-HF-lite pricing pre-registration after M3219 smoke"
    next_connectors = [
        (
            "Keep the explicit Chrono backend variant selector under reset-step smoke coverage."
            if has_selector
            else "Add an explicit Chrono backend variant selector (vehicle model + tire model or JSON fixture)."
        ),
        "Expose reset-time backend_info with selected model, tire model, mass, max steer, wheelbase, chassis inertia, and tire family.",
        "Map or deliberately bracket lateral channels: lf/lr/CG placement, Iz/inertia, axle load split, and tire curve family.",
        "Run a no-policy reset/step smoke for at least Sedan nominal plus two passenger-like variants before S4 pricing.",
        "Freeze S4-HF-lite seed streams and report as pricing only; no RL, no driver-performance claim.",
    ]
    return {
        "schema_version": 1,
        "milestone": "m3218-s4-hf-lite-backend-inventory-preflight",
        "claim_boundary": {
            "allowed": [
                "Chrono resource inventory",
                "current backend wiring audit",
                "admission decision for the next S4-HF-lite connector milestone",
            ],
            "forbidden": [
                "driver performance",
                "high-fidelity sufficiency",
                "S4/C5 pricing result",
                "RL evidence",
                "validation ranking or promotion claim",
            ],
        },
        "chrono_probe": chrono_probe,
        "current_backend": backend,
        "decision": {
            "direct_s4_hf_lite_pricing_admitted_now": direct_pricing,
            "chrono_resources_support_extension": extension_supported,
            "chrono_resource_summary": (
                "Chrono data and Python wrappers contain multiple vehicle/tire resources."
                if extension_supported
                else "Chrono resource availability was not sufficient to admit a multi-vehicle extension from this preflight."
            ),
            "blocker": blocker,
            "next_admitted_milestone": next_step,
            "minimal_connectors": next_connectors,
        },
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_markdown(path: Path, report: dict[str, Any], json_path: Path) -> None:
    chrono = report["chrono_probe"]
    backend = report["current_backend"]
    decision = report["decision"]
    candidates = chrono.get("candidate_passenger_like_models", []) if chrono.get("ok") else []
    tire_attrs = chrono.get("tire_model_attrs", []) if chrono.get("ok") else []

    lines = [
        "# M3218 S4-HF-lite Backend Inventory Preflight",
        "",
        "Status: completed. This is a zero-rollout infrastructure preflight for the S4-HF-lite route; it is not a pricing run, not a driver-performance result, and not RL evidence.",
        "",
        "## Verdict",
        "",
        f"- Direct S4-HF-lite pricing admitted now: **{str(decision['direct_s4_hf_lite_pricing_admitted_now']).lower()}**.",
        f"- Reason: {decision['blocker']}",
        f"- Next admitted milestone: {decision['next_admitted_milestone']}.",
        "",
        "## What Chrono Provides",
        "",
    ]
    if chrono.get("ok"):
        lines.extend(
            [
                f"- Chrono vehicle data path: `{chrono.get('vehicle_data_path')}`.",
                f"- Vehicle JSON files visible: {chrono.get('vehicle_json_count')}; vehicle module classes visible: {chrono.get('vehicle_module_class_count')}.",
                "- Passenger-like data candidates found: "
                + (", ".join(f"`{item['model']}`" for item in candidates) if candidates else "none"),
                "- Tire model attributes visible: "
                + (", ".join(f"`{item}`" for item in tire_attrs) if tire_attrs else "none"),
            ]
        )
    else:
        lines.extend(
            [
                "- Chrono probe failed; see the JSON artifact for stdout/stderr.",
                f"- Probe error: `{chrono.get('error', 'unknown')}`.",
            ]
        )
    lines.extend(
        [
            "",
            "## What Is Actually Wired",
            "",
            f"- Backend id: `{backend['backend_id']}`.",
            f"- Backend source: `{backend['backend_path']}`; worker: `{backend['worker_path']}`.",
            f"- Hard-coded `veh.Sedan()`: {backend['hardcoded_sedan_constructor']}.",
            f"- Hard-coded `TireModelType_TMEASY`: {backend['hardcoded_tmeasy_tire']}.",
            f"- Runtime vehicle/tire variant selector present: {backend['has_runtime_vehicle_variant_selector']}.",
            f"- Scenario carries `lf/lr/iz/cf/cr`: {backend['scenario_carries_lateral_params']}, but they are not mapped into Chrono dynamics.",
            "",
            "| channel | current status | note |",
            "|---|---|---|",
        ]
    )
    for row in backend["current_mapping"]:
        lines.append(f"| `{row['channel']}` | `{row['status']}` | {row['note']} |")
    lines.extend(
        [
            "",
            "## Minimal Next Connectors",
            "",
        ]
    )
    for item in decision["minimal_connectors"]:
        lines.append(f"- {item}")
    try:
        json_display = str(json_path.relative_to(REPO_ROOT))
    except ValueError:
        json_display = str(json_path)
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "Allowed: Chrono resource inventory, current backend wiring audit, and admission of the next connector milestone.",
            "",
            "Rejected explicitly: driver-performance, high-fidelity sufficiency, S4/C5 pricing result, RL evidence, validation/ranking/promotion, paper evidence, or any mutation of the deployed v4 incumbent.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_display}`",
            f"- Script: `scripts/feasibility_audit/{Path(__file__).name}`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--timeout-s", type=float, default=60.0)
    parser.add_argument(
        "--chrono-launch",
        nargs="+",
        default=["conda", "run", "--no-capture-output", "-n", "chrono", "python"],
        help="Command prefix used to launch the chrono-env Python interpreter.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    chrono_probe = _run_chrono_probe(list(args.chrono_launch), args.timeout_s)
    backend = _inspect_current_backend()
    report = _build_report(chrono_probe, backend)
    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    doc = args.doc if args.doc.is_absolute() else REPO_ROOT / args.doc
    _write_json(output, report)
    _write_markdown(doc, report, output)
    print(json.dumps(report["decision"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
