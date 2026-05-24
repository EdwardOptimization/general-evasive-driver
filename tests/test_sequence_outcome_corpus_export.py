import csv

from autodrift.sequence_outcome_corpus_export import (
    classify_sequence_outcome_corpus,
    export_sequence_outcome_corpus,
)


HEADER = [
    "source_index",
    "source_role",
    "proposal_id",
    "selected_index",
    "seed",
    "step",
    "preferred_snapshot_id",
    "wrong_snapshot_id",
    "preferred_fault",
    "preferred_fault_family",
    "preferred_fault_severity",
    "wrong_fault",
    "wrong_fault_family",
    "wrong_fault_severity",
    "fault_family_pair",
    "severity_pair",
    "source_pool",
    "assigned_split",
    "step_bucket",
    "obstacle_distance_bucket",
    "variant",
    "horizon",
    "normal_success",
    "normal_margin",
    "variant_success",
    "variant_margin",
    "margin_gap_from_normal",
    "success_drop_from_normal",
    "first_steer",
    "first_throttle",
    "first_brake",
    "trajectory_l2_mean",
    "trajectory_l2_max",
    "prefix_l2_mean",
    "prefix_l2_max",
    "prefix_compare_steps",
    "terminal_reason",
    "sequence_action_critical",
    "sequence_outcome_critical",
    "temporal_action_critical",
    "temporal_outcome_critical",
    "sentinel",
]


def _row(**overrides):
    row = {
        "source_index": "1",
        "source_role": "primary",
        "proposal_id": "11",
        "selected_index": "0",
        "seed": "101",
        "step": "12",
        "preferred_snapshot_id": "20",
        "wrong_snapshot_id": "22",
        "preferred_fault": "front_drop",
        "preferred_fault_family": "front_lateral_authority_drop",
        "preferred_fault_severity": "severe",
        "wrong_fault": "steering_fault",
        "wrong_fault_family": "steering_fault",
        "wrong_fault_severity": "severe",
        "fault_family_pair": "front_lateral_authority_drop->steering_fault",
        "severity_pair": "severe->severe",
        "source_pool": "test",
        "assigned_split": "public",
        "step_bucket": "1",
        "obstacle_distance_bucket": "0",
        "variant": "normal",
        "horizon": "4",
        "normal_success": "True",
        "normal_margin": "0.10",
        "variant_success": "True",
        "variant_margin": "0.10",
        "margin_gap_from_normal": "0.0",
        "success_drop_from_normal": "False",
        "first_steer": "0.1",
        "first_throttle": "-0.2",
        "first_brake": "0.3",
        "trajectory_l2_mean": "0.0",
        "trajectory_l2_max": "0.0",
        "prefix_l2_mean": "0.0",
        "prefix_l2_max": "0.0",
        "prefix_compare_steps": "4",
        "terminal_reason": "obstacle_completed",
        "sequence_action_critical": "False",
        "sequence_outcome_critical": "False",
        "temporal_action_critical": "False",
        "temporal_outcome_critical": "False",
        "sentinel": "False",
    }
    row.update({key: str(value) for key, value in overrides.items()})
    return row


def _write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_export_filters_sentinel_and_action_only_rows(tmp_path):
    normal = _row()
    positive = _row(
        variant="zero_command_obs",
        variant_margin="0.05",
        margin_gap_from_normal="0.05",
        sequence_action_critical="True",
        sequence_outcome_critical="True",
        temporal_action_critical="True",
        temporal_outcome_critical="True",
        prefix_l2_mean="0.04",
    )
    action_only = _row(
        variant="command_shift_obs",
        variant_margin="0.09",
        margin_gap_from_normal="0.01",
        sequence_action_critical="True",
        sequence_outcome_critical="False",
        temporal_action_critical="True",
        temporal_outcome_critical="False",
        prefix_l2_mean="0.03",
    )
    sentinel_positive = _row(
        source_index="2",
        source_role="sentinel",
        seed="202",
        variant="zero_command_obs",
        sequence_action_critical="True",
        sequence_outcome_critical="True",
        temporal_action_critical="True",
        temporal_outcome_critical="True",
        sentinel="True",
    )
    rollouts = tmp_path / "rollouts.csv"
    critical = tmp_path / "critical.csv"
    sentinels = tmp_path / "sentinels.csv"
    _write_csv(rollouts, [normal, positive, action_only, sentinel_positive])
    _write_csv(critical, [positive, action_only, sentinel_positive])
    _write_csv(sentinels, [sentinel_positive])
    summary = tmp_path / "summary.json"
    summary.write_text("{}\n", encoding="utf-8")

    result = export_sequence_outcome_corpus(
        summary_path=summary,
        rollouts_path=rollouts,
        sequence_critical_rows_path=critical,
        sentinel_rows_path=sentinels,
        run_dir=tmp_path / "run",
        min_positive_rows=1,
        min_unique_positive_seeds=1,
        min_unique_positive_fault_family_pairs=1,
        max_allowed_positive_seed_dominance=1.0,
    )

    assert result["positive_rows"] == 1
    assert result["excluded_sentinel_rows"] == 1
    assert result["hard_negative_rows"] == 1
    assert result["result_class"] == "sequence_outcome_corpus_exported"

    positives = _read_csv(tmp_path / "run" / "positive_sequence_outcomes.csv")
    assert [row["variant"] for row in positives] == ["zero_command_obs"]
    assert positives[0]["proof_positive"] == "True"

    contrast_roles = [row["contrast_role"] for row in _read_csv(tmp_path / "run" / "contrast_rows.csv")]
    assert contrast_roles == ["normal", "positive_intervention", "hard_negative_action_only"]


def test_classify_sequence_outcome_corpus_rejects_artifacts_before_balance():
    assert (
        classify_sequence_outcome_corpus(
            positive_rows=100,
            positive_sentinel_rows=1,
            positive_source_role_sentinel_rows=0,
            duplicate_positive_keys=0,
            missing_normal_matches=0,
            unique_positive_seeds=50,
            unique_positive_fault_family_pairs=10,
            max_positive_seed_dominance=0.02,
        )
        == "sequence_outcome_corpus_artifact"
    )


def test_classify_sequence_outcome_corpus_reports_unbalanced():
    assert (
        classify_sequence_outcome_corpus(
            positive_rows=100,
            positive_sentinel_rows=0,
            positive_source_role_sentinel_rows=0,
            duplicate_positive_keys=0,
            missing_normal_matches=0,
            unique_positive_seeds=3,
            unique_positive_fault_family_pairs=10,
            max_positive_seed_dominance=0.40,
        )
        == "sequence_outcome_corpus_unbalanced"
    )
