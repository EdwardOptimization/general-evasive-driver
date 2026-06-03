from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np

from autodrift import paper_route_current_sim_dual_axis_scenario_distribution_support_atlas as atlas
from autodrift.artifacts import read_json, write_csv_rows, write_json


CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "candidate_group",
    "source_panel_id",
    "source_panel_class",
    "source_panel_scope",
    "role_family",
    "sampled_obstacle_label",
    "hidden_dynamics_bucket",
    "obstacle_longitudinal_timing_bucket",
    "obstacle_lateral_offset_bucket",
    "geometry_lever_class",
    "boundary_protocol_class",
    "split",
    "episode_count",
    "actual_success_rate",
    "hard_offtrack_rate",
    "collision_rate",
    "labels_enter_actor_input",
    "actor_input_contract_changed",
    "scenario_redesign_executed",
    "policy_action_executed",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
    "reason",
]


class _FakeConfig:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = deepcopy(data)


class _FakeScenario:
    def __init__(self, label: str) -> None:
        self.label = label


class _FakeEnv:
    def __init__(self, config: _FakeConfig) -> None:
        self.config = config
        self.obstacle_scenario = None
        self.step_count = 0

    def reset(self, *, seed: int) -> tuple[np.ndarray, dict[str, Any]]:
        data = self.config.data
        obstacle = dict(data.get("obstacle") or {})
        labels = list(obstacle.get("allowed_labels", []))
        cell_is_partial = labels == ["aes_feasible"] or labels == ["drift_required"]
        success = not cell_is_partial or int(seed) % 2 == 0
        if not success:
            raise RuntimeError("failed to sample an obstacle scenario matching the configured filters")
        label = labels[0] if labels and labels[0] != "aeb_feasible" else "aeb_feasible"
        if len(labels) > 1:
            label = "aes_feasible"
        self.obstacle_scenario = _FakeScenario(label)
        return np.ones(72, dtype=np.float64), {
            "initial_mu": 0.8,
            "mu": 0.8,
            "mass_scale": 1.0,
            "tire_stiffness_scale": 1.0,
            "brake_scale": 1.0,
            "steer_tau_scale": 1.0,
            "drive_tau_scale": 1.0,
            "speed_ref": 12.0,
            "obstacle_distance": 25.0,
            "obstacle_lateral_offset": 0.1,
            "active_obstacle_half_width": 0.7,
            "obstacle_threshold_score": 0.2,
        }

    def close(self) -> None:
        return None


def _candidate_row(candidate_id: str, candidate_group: str) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "candidate_group": candidate_group,
        "source_panel_id": "source-panel",
        "source_panel_class": "scenario_quality_blocker",
        "source_panel_scope": "scope",
        "role_family": "",
        "sampled_obstacle_label": "",
        "hidden_dynamics_bucket": "",
        "obstacle_longitudinal_timing_bucket": "",
        "obstacle_lateral_offset_bucket": "",
        "geometry_lever_class": "",
        "boundary_protocol_class": "guardrail_not_winner",
        "split": "public_debug",
        "episode_count": 1,
        "actual_success_rate": 0.0,
        "hard_offtrack_rate": 1.0,
        "collision_rate": 0.0,
        "labels_enter_actor_input": False,
        "actor_input_contract_changed": False,
        "scenario_redesign_executed": False,
        "policy_action_executed": False,
        "repair_execution_started": False,
        "training_started": False,
        "ranking_admissible": False,
        "winner_selected": False,
        "reason": "fixture",
    }


def _write_sources(root: Path, *, include_candidates: bool = True) -> tuple[Path, Path, Path]:
    m2455 = root / "m2455"
    m2466 = root / "m2466"
    m2455.mkdir(parents=True)
    m2466.mkdir(parents=True)
    write_json(
        m2455 / "summary.json",
        {
            "result_class": "current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight_pass",
            "candidate_row_count": 30 if include_candidates else 0,
            "stable_feasibility_support_count": 3 if include_candidates else 0,
            "stable_aes_support_count": 3 if include_candidates else 0,
            "handling_limit_guardrail_count": 5 if include_candidates else 0,
            "hidden_dynamics_guardrail_count": 9 if include_candidates else 0,
            "mitigation_guardrail_count": 3 if include_candidates else 0,
            "guardrail_violation_count": 0,
        },
    )
    rows: list[dict[str, Any]] = []
    if include_candidates:
        for group, count in [
            ("stable_feasibility_support", 3),
            ("stable_aes_support", 3),
            ("handling_limit_guardrail", 5),
            ("hidden_dynamics_guardrail", 9),
            ("mitigation_guardrail", 3),
        ]:
            for index in range(count):
                rows.append(_candidate_row(f"{group}_{index:03d}", group))
    write_csv_rows(m2455 / "candidate_rows.csv", rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_json(
        m2466 / "summary.json",
        {
            "result_class": "scenario_quality_r1_reset_sampling_diagnostic_panel_complete",
            "diagnostic_classification": "seed_fragility",
            "guardrail_violation_count": 0,
        },
    )
    doc = root / "m2467.md"
    doc.write_text("M2467 audit fixture\n", encoding="utf-8")
    return m2455, m2466, doc


def test_scenario_distribution_support_atlas_writes_broad_reset_only_panel(
    tmp_path: Path,
    monkeypatch,
) -> None:
    m2455, m2466, doc = _write_sources(tmp_path)
    monkeypatch.setattr(atlas, "build_env_config", lambda data: _FakeConfig(data))
    monkeypatch.setattr(atlas, "AutoDriftEnv", _FakeEnv)

    summary = atlas.run_scenario_distribution_support_atlas(
        m2455_dir=m2455,
        m2466_dir=m2466,
        m2467_doc=doc,
        output_dir=tmp_path / "out",
        seed_base=100,
        seeds_per_cell=2,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == atlas.RESULT_COMPLETE
    assert summary["atlas_cell_count"] >= 12
    assert summary["candidate_group_coverage_count"] == 5
    assert summary["fixed_m2464_r1_reuse_count"] == 0
    assert summary["diagnostic_attempt_count"] == summary["atlas_cell_count"] * 2
    assert summary["environment_step_count"] == 0
    assert summary["policy_action_executed"] is False
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected_count"] == 0
    assert "distribution_support_atlas" in summary["atlas_classification"]
    assert "seed_fragility" in summary["atlas_classification"]

    output = Path(summary["output_dir"])
    cell_rows = atlas.read_csv_rows(output / "atlas_cell_rows.csv")
    reset_rows = atlas.read_csv_rows(output / "reset_rows.csv")
    class_rows = atlas.read_csv_rows(output / "classification_rows.csv")
    assert len(cell_rows) == summary["atlas_cell_count"]
    assert len(reset_rows) == summary["diagnostic_attempt_count"]
    assert all(row["diagnostic_only"] == "True" for row in cell_rows)
    assert all(row["matches_fixed_m2464_r1_overlay"] == "False" for row in cell_rows)
    assert all(row["environment_step_count"] == "0" for row in reset_rows)
    assert {row["classification_key"] for row in class_rows} >= {
        "distribution_cell_count",
        "reset_support_partial_cell_count",
    }
    assert read_json(output / "run_state.json")["status"] == "completed"


def test_scenario_distribution_support_atlas_fails_closed_without_candidates(tmp_path: Path) -> None:
    m2455, m2466, doc = _write_sources(tmp_path, include_candidates=False)

    summary = atlas.run_scenario_distribution_support_atlas(
        m2455_dir=m2455,
        m2466_dir=m2466,
        m2467_doc=doc,
        output_dir=tmp_path / "out",
        seed_base=100,
        seeds_per_cell=2,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == atlas.RESULT_FAIL
    assert summary["source_admission_failure_count"] > 0
    assert summary["diagnostic_attempt_count"] == 0
    assert summary["guardrail_violation_count"] > 0
    assert summary["atlas_classification"] == "atlas_incomplete"
