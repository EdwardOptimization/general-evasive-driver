from pathlib import Path

from autodrift.v4_reset_source_sequence_intervention import (
    classify_v4_reset_sequence_result,
    load_v4_reset_source_rows,
)


HEADER = (
    "pair_id,preferred_snapshot_id,wrong_snapshot_id,seed,step,preferred_fault,"
    "preferred_fault_family,preferred_fault_severity,wrong_fault,wrong_fault_family,"
    "wrong_fault_severity,feature_distance,normal_margin,wrong_margin,reset_margin,"
    "history_margin_gap,reset_margin_gap,success_drop,reset_success_drop,action_l2_gap,"
    "reset_action_l2_gap,history_action_critical,wrong_history_action_critical,"
    "reset_history_action_critical,assigned_split,acceptance_reason,rejection_reason,"
    "match_distance,pairing_mode,pairing_rule\n"
)


def _write(path: Path, rows: list[dict[str, object]]) -> None:
    keys = HEADER.strip().split(",")
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(HEADER)
        for row in rows:
            handle.write(",".join(str(row.get(key, "")) for key in keys) + "\n")


def _row(**overrides):
    row = {
        "pair_id": 1,
        "preferred_snapshot_id": 10,
        "wrong_snapshot_id": 20,
        "seed": 76000,
        "step": 24,
        "preferred_fault": "front_lateral_drop",
        "preferred_fault_family": "front_lateral_authority_drop",
        "preferred_fault_severity": "severe",
        "wrong_fault": "steering_lag",
        "wrong_fault_family": "steering_fault",
        "wrong_fault_severity": "severe",
        "feature_distance": 0.1,
        "normal_margin": 1.0,
        "wrong_margin": 1.0,
        "reset_margin": 0.97,
        "history_margin_gap": 0.0,
        "reset_margin_gap": 0.03,
        "success_drop": "False",
        "reset_success_drop": "False",
        "action_l2_gap": 0.0,
        "reset_action_l2_gap": 0.03,
        "history_action_critical": "True",
        "wrong_history_action_critical": "False",
        "reset_history_action_critical": "True",
        "assigned_split": "train",
        "acceptance_reason": "reset_only_history_action_critical",
        "rejection_reason": "",
        "match_distance": 0.1,
        "pairing_mode": "cross_fault",
        "pairing_rule": "front_lateral_authority_drop->steering_fault",
    }
    row.update(overrides)
    return row


def test_load_v4_reset_source_rows_selects_primary_and_sentinel(tmp_path):
    reset_rows = tmp_path / "reset.csv"
    rejected_rows = tmp_path / "rejected.csv"
    _write(reset_rows, [_row(pair_id=1), _row(pair_id=2, seed=76001, reset_action_l2_gap=0.001)])
    _write(
        rejected_rows,
        [
            _row(
                pair_id=3,
                seed=76002,
                reset_action_l2_gap=0.018,
                reset_margin_gap=0.005,
                action_l2_gap=0.001,
                rejection_reason="history_insensitive_too_mild",
                reset_history_action_critical="False",
            )
        ],
    )

    rows = load_v4_reset_source_rows(
        reset_rows_path=reset_rows,
        rejected_rows_path=rejected_rows,
        seed_start=76000,
        seed_count=10,
        max_source_rows=4,
        min_action_l2_gap=0.015,
        sentinel_fraction=0.25,
    )

    assert [row["source_role"] for row in rows] == ["primary", "sentinel"]
    assert rows[0]["fault_family_pair"] == "front_lateral_authority_drop->steering_fault"
    assert rows[0]["source_index"] == 0
    assert rows[0]["source_kind"] == "v4_reset_source"
    assert rows[0]["claim_boundary_level"] == "current_model_or_proxy"
    assert rows[1]["source_pool"] == "m749_v4_history_insensitive"


def test_classify_v4_reset_sequence_result_maps_base_classes():
    assert (
        classify_v4_reset_sequence_result(result_class="sequence_outcome_positive")
        == "v4_reset_sequence_outcome_positive"
    )
    assert classify_v4_reset_sequence_result(result_class="sequence_action_only") == "v4_reset_sequence_action_only"
