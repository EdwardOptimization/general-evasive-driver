"""Deterministic candidate templates for support-first executable v2 source mining."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import utc_timestamp, write_json
from autodrift.executable_v2_task_source_metadata_redesign import (
    ROLE_DRIFT_REQUIRED,
    ROLE_STABLE_AEB,
    ROLE_STABLE_AES,
    ROLE_UNAVOIDABLE,
)


TEMPLATE_ID = "support_first_candidate_templates_v0"
DEFAULT_OUTPUT_PATH = Path("configs/executable_v2_support_first_candidate_templates_v0.json")
SPEEDS = (10.0, 14.0, 18.0, 22.0, 26.0, 30.0)
MU_VALUES = (0.25, 0.40, 0.60, 0.80, 1.00, 1.15)
SURFACES = (
    {
        "surface_variant": "steady_surface",
        "source_family_id": "steady_surface",
        "friction_step_enabled": False,
        "friction_step_at": "",
        "dt": 0.05,
        "min_time_after_friction_step": 0.0,
    },
    {
        "surface_variant": "post_friction_step",
        "source_family_id": "post_friction_step",
        "friction_step_enabled": True,
        "friction_step_at": 20,
        "dt": 0.05,
        "min_time_after_friction_step": 0.30,
    },
)
ROLE_SETTINGS: dict[str, dict[str, Any]] = {
    ROLE_STABLE_AEB: {
        "source_required_label": "aeb_feasible",
        "source_allowed_labels": "aeb_feasible",
        "require_aeb_infeasible": False,
        "obstacle_distance_min": 10.0,
        "obstacle_distance_max": 95.0,
        "obstacle_distance_count": 86,
        "obstacle_half_width_min": 0.20,
        "obstacle_half_width_max": 1.40,
        "obstacle_half_width_count": 25,
        "min_accepted_cells": 10,
        "recovery_horizon_required": False,
        "mitigation_metric_contract_present": False,
    },
    ROLE_STABLE_AES: {
        "source_required_label": "aes_feasible",
        "source_allowed_labels": "aes_feasible",
        "require_aeb_infeasible": True,
        "obstacle_distance_min": 8.0,
        "obstacle_distance_max": 70.0,
        "obstacle_distance_count": 63,
        "obstacle_half_width_min": 0.20,
        "obstacle_half_width_max": 1.40,
        "obstacle_half_width_count": 25,
        "min_accepted_cells": 10,
        "recovery_horizon_required": False,
        "mitigation_metric_contract_present": False,
    },
    ROLE_DRIFT_REQUIRED: {
        "source_required_label": "drift_required",
        "source_allowed_labels": "drift_required",
        "require_aeb_infeasible": True,
        "obstacle_distance_min": 5.0,
        "obstacle_distance_max": 55.0,
        "obstacle_distance_count": 51,
        "obstacle_half_width_min": 0.20,
        "obstacle_half_width_max": 1.60,
        "obstacle_half_width_count": 29,
        "min_accepted_cells": 10,
        "recovery_horizon_required": True,
        "mitigation_metric_contract_present": False,
    },
    ROLE_UNAVOIDABLE: {
        "source_required_label": "unavoidable",
        "source_allowed_labels": "unavoidable",
        "require_aeb_infeasible": True,
        "obstacle_distance_min": 2.0,
        "obstacle_distance_max": 35.0,
        "obstacle_distance_count": 34,
        "obstacle_half_width_min": 0.20,
        "obstacle_half_width_max": 2.00,
        "obstacle_half_width_count": 37,
        "min_accepted_cells": 10,
        "recovery_horizon_required": False,
        "mitigation_metric_contract_present": True,
    },
}


def _tag_float(prefix: str, value: float) -> str:
    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return prefix + text.replace(".", "p")


def _profile_control_hash(row: Mapping[str, Any]) -> str:
    keys = [
        "template_id",
        "source_role_semantics",
        "speed_ref",
        "mu",
        "surface_variant",
        "friction_step_enabled",
        "friction_step_at",
        "dt",
        "min_time_after_friction_step",
        "obstacle_distance_min",
        "obstacle_distance_max",
        "obstacle_distance_count",
        "obstacle_half_width_min",
        "obstacle_half_width_max",
        "obstacle_half_width_count",
        "min_accepted_cells",
        "recovery_horizon_required",
        "mitigation_metric_contract_present",
    ]
    payload = {key: row.get(key, "") for key in keys}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _candidate_row(*, role: str, speed: float, mu: float, surface: Mapping[str, Any]) -> dict[str, Any]:
    settings = dict(ROLE_SETTINGS[role])
    speed_tag = _tag_float("v", speed)
    mu_tag = _tag_float("mu", mu)
    source_id = f"sfm_v0_{role}_{surface['surface_variant']}_{speed_tag}_{mu_tag}"
    row: dict[str, Any] = {
        "template_id": TEMPLATE_ID,
        "candidate_source_id": source_id,
        "source_v1_bounded_panel_spec_id": source_id,
        "source_scenario_spec_id": f"{source_id}_scenario",
        "source_family_id": surface["source_family_id"],
        "surface_variant": surface["surface_variant"],
        "source_role_semantics": role,
        "profile_name": f"{role}_{surface['surface_variant']}_grid_v0",
        "profile_group": role,
        "speed_ref": float(speed),
        "mu": float(mu),
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "ego_half_width": 0.90,
        "safety_margin": 0.30,
        "brake_mu_fraction": 0.90,
        "conventional_lateral_mu_fraction": 0.42,
        "drift_lateral_mu_fraction": 0.85,
        "gravity": 9.81,
        **surface,
        **settings,
    }
    row["profile_control_hash"] = _profile_control_hash(row)
    return row


def generate_v0_candidate_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for role in (ROLE_STABLE_AEB, ROLE_STABLE_AES, ROLE_DRIFT_REQUIRED, ROLE_UNAVOIDABLE):
        for surface in SURFACES:
            for speed in SPEEDS:
                for mu in MU_VALUES:
                    rows.append(_candidate_row(role=role, speed=speed, mu=mu, surface=surface))
    return rows


def summarize_candidate_rows(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    role_counts = Counter(str(row["source_role_semantics"]) for row in rows)
    speed_counts = Counter(str(row["speed_ref"]) for row in rows)
    mu_counts = Counter(str(row["mu"]) for row in rows)
    surface_counts = Counter(str(row["surface_variant"]) for row in rows)
    source_family_counts = Counter(str(row["source_family_id"]) for row in rows)
    grid_cell_count_total = sum(
        int(row["obstacle_distance_count"]) * int(row["obstacle_half_width_count"]) for row in rows
    )
    return {
        "template_id": TEMPLATE_ID,
        "candidate_row_count": len(rows),
        "role_counts": dict(sorted(role_counts.items())),
        "speed_counts": dict(sorted(speed_counts.items(), key=lambda item: float(item[0]))),
        "mu_counts": dict(sorted(mu_counts.items(), key=lambda item: float(item[0]))),
        "surface_counts": dict(sorted(surface_counts.items())),
        "source_family_counts": dict(sorted(source_family_counts.items())),
        "grid_cell_count_total": int(grid_cell_count_total),
        "labels_enter_actor_input_count": sum(bool(row.get("labels_enter_actor_input")) for row in rows),
        "ranking_admissible_by_default_count": sum(bool(row.get("v2_ranking_admissible_by_default")) for row in rows),
        "materialized_row_count": 0,
        "project_artifact_source_mining_run": False,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "guardrail_violation_count": 0,
    }


def build_v0_template_payload() -> dict[str, Any]:
    rows = generate_v0_candidate_rows()
    return {
        "template_id": TEMPLATE_ID,
        "generated_at_utc": utc_timestamp(),
        "candidate_sources": rows,
        "summary": summarize_candidate_rows(rows),
    }


def write_v0_template(path: Path | str = DEFAULT_OUTPUT_PATH) -> dict[str, Any]:
    payload = build_v0_template_payload()
    write_json(path, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    payload = write_v0_template(args.output)
    summary = payload["summary"]
    print(f"template={args.output}")
    print(f"template_id={summary['template_id']}")
    print(f"candidate_row_count={summary['candidate_row_count']}")
    print(f"grid_cell_count_total={summary['grid_cell_count_total']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
