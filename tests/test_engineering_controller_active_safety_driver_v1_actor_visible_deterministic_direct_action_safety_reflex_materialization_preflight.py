from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows
import autodrift.engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight as m3078


def _write_sources(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    m3077_design = tmp_path / "m3077.md"
    m3076_audit = tmp_path / "m3076.md"
    m3067_dir = tmp_path / "m3067"
    m3075_dir = tmp_path / "m3075"
    m3067_dir.mkdir()
    m3075_dir.mkdir()
    m3077_design.write_text("# M3077\n", encoding="utf-8")
    m3076_audit.write_text("# M3076\n", encoding="utf-8")
    write_json(
        m3067_dir / "summary.json",
        {
            "measurement_success_count": 8,
            "measurement_collision_count": 4,
            "measurement_offtrack_count": 16,
            "measurement_speed_too_low_count": 5,
        },
    )
    write_json(
        m3075_dir / "summary.json",
        {
            "measurement_success_count": 6,
            "measurement_collision_count": 4,
            "measurement_offtrack_count": 19,
            "measurement_speed_too_low_count": 4,
        },
    )
    return m3077_design, m3076_audit, m3067_dir, m3075_dir


def test_actor_visible_safety_reflex_action_is_bounded_and_direct() -> None:
    observation = np.zeros(72, dtype=np.float32)
    observation[13:28:2] = 0.15
    observation[29:44:2] = -0.15
    action = m3078.actor_visible_safety_reflex_action(observation)

    assert action.shape == (3,)
    assert np.all(np.isfinite(action))
    assert float(np.max(np.abs(action))) <= 1.0

    obstacle_ahead = observation.copy()
    obstacle_ahead[44] = 1.0
    obstacle_ahead[45] = 0.10
    obstacle_ahead[46] = 0.0
    obstacle_action = m3078.actor_visible_safety_reflex_action(obstacle_ahead)

    assert obstacle_action[1] < action[1]
    assert obstacle_action[2] > action[2]


def test_materialize_safety_reflex_artifacts_preserves_actor_contract(tmp_path: Path) -> None:
    m3077_design, m3076_audit, m3067_dir, m3075_dir = _write_sources(tmp_path)
    output_dir = tmp_path / "m3078"
    follow_up_manifest = tmp_path / "m3079.json"
    doc_path = tmp_path / "m3078.md"

    summary = m3078.materialize(
        m3077_design=m3077_design,
        m3076_audit=m3076_audit,
        m3067_dir=m3067_dir,
        m3075_dir=m3075_dir,
        output_dir=output_dir,
        follow_up_manifest=follow_up_manifest,
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["observation_shape"] == 72
    assert summary["action_shape"] == 3
    assert summary["runtime_base_policy_required"] is False
    assert summary["direct_action_contract_pass"] is True
    assert summary["environment_reset_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    feature_rows = read_csv_rows(output_dir / "actor_visible_feature_contract_rows.csv")
    covered = set()
    for row in feature_rows:
        assert row["actor_visible"] == "True"
        assert row["hidden_oracle_required"] == "False"
        covered.update(range(int(row["slice_start"]), int(row["slice_end_exclusive"])))
    assert covered == set(range(72))

    rule_rows = read_csv_rows(output_dir / "safety_reflex_rule_rows.csv")
    assert {row["runtime_base_policy_required"] for row in rule_rows} == {"False"}
    assert {row["direct_action_output"] for row in rule_rows} == {"True"}

    exclusion_rows = read_csv_rows(output_dir / "actor_input_exclusion_rows.csv")
    assert all(row["materialized_in_actor_input"] == "False" for row in exclusion_rows)
    assert all(row["status_pass"] == "True" for row in exclusion_rows)

    admission_rows = read_csv_rows(output_dir / "measurement_admission_gate_rows.csv")
    assert {row["same_denominator_required"] for row in admission_rows} == {"True"}

    policy_config = read_json(output_dir / "direct_action_policy_config.json")
    assert policy_config["observation_shape"] == 72
    assert policy_config["action_shape"] == 3
    assert policy_config["runtime_base_policy_required"] is False

    follow_up = read_json(follow_up_manifest)
    assert follow_up["id"] == m3078.NEXT_ID
    assert follow_up["status"] == "pending"
