import csv
import json

from autodrift.v3_sequence_outcome_corpus_export import (
    V3_ROLLOUT_FIELDS,
    classify_v3_sequence_outcome_corpus,
    export_v3_sequence_outcome_corpus,
)


def _row(**overrides):
    row = {field: "" for field in V3_ROLLOUT_FIELDS}
    row.update(
        {
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
            "wrong_fault": "steering_lag",
            "wrong_fault_family": "steering_fault",
            "wrong_fault_severity": "moderate",
            "fault_family_pair": "front_lateral_authority_drop->steering_fault",
            "severity_pair": "severe->moderate",
            "source_pool": "m740_reset_only",
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
            "pair_id": "pair-1",
            "pairing_rule": "test_rule",
            "reset_action_l2_gap": "0.02",
            "reset_margin_gap": "0.03",
            "history_margin_gap": "0.04",
            "action_l2_gap": "0.05",
            "match_distance": "0.06",
            "feature_distance": "0.07",
            "acceptance_reason": "accepted",
            "rejection_reason": "",
            "source_kind": "v3_reset_source",
        }
    )
    row.update({key: str(value) for key, value in overrides.items()})
    return row


def _write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=V3_ROLLOUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_fault_config(path):
    path.write_text(
        json.dumps(
            {
                "notes": "test claim boundary",
                "claim_boundary": {
                    "current_model_fault": "represented",
                    "current_model_proxy": "proxy",
                    "future_only_fault": "future",
                },
                "future_only_faults": ["true_single_wheel_blowout"],
                "faults": [
                    {
                        "name": "front_drop",
                        "family": "front_lateral_authority_drop",
                        "severity": "severe",
                        "fidelity_class": "current_model_proxy",
                        "params": {"cf_scale": 0.2},
                    },
                    {
                        "name": "steering_lag",
                        "family": "steering_fault",
                        "severity": "moderate",
                        "fidelity_class": "current_model_fault",
                        "params": {"steer_tau_scale": 2.0},
                    },
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_export_filters_sentinel_and_preserves_v3_metadata(tmp_path):
    normal = _row()
    positive = _row(
        variant="zero_command_obs",
        variant_margin="-0.02",
        margin_gap_from_normal="0.12",
        success_drop_from_normal="True",
        sequence_action_critical="True",
        sequence_outcome_critical="True",
        prefix_l2_mean="0.04",
    )
    action_only = _row(
        variant="command_shift_obs",
        variant_margin="0.09",
        margin_gap_from_normal="0.01",
        sequence_action_critical="True",
        sequence_outcome_critical="False",
        prefix_l2_mean="0.03",
    )
    sentinel_positive = _row(
        source_index="2",
        source_role="sentinel",
        seed="202",
        pair_id="pair-2",
        variant="zero_command_obs",
        sequence_action_critical="True",
        sequence_outcome_critical="True",
        sentinel="True",
    )
    rollouts = tmp_path / "rollouts.csv"
    critical = tmp_path / "critical.csv"
    sentinels = tmp_path / "sentinels.csv"
    config = tmp_path / "faults.json"
    _write_csv(rollouts, [normal, positive, action_only, sentinel_positive])
    _write_csv(critical, [positive, action_only, sentinel_positive])
    _write_csv(sentinels, [sentinel_positive])
    _write_fault_config(config)
    source_summary = tmp_path / "summary.json"
    source_summary.write_text('{"result_class":"v3_reset_sequence_outcome_positive"}\n', encoding="utf-8")

    result = export_v3_sequence_outcome_corpus(
        summary_path=source_summary,
        rollouts_path=rollouts,
        sequence_critical_rows_path=critical,
        sentinel_rows_path=sentinels,
        fault_config_path=config,
        run_dir=tmp_path / "run",
        min_positive_rows=1,
        min_unique_positive_seeds=1,
        min_unique_positive_fault_family_pairs=1,
        max_allowed_positive_seed_dominance=1.0,
    )

    assert result["positive_rows"] == 1
    assert result["excluded_sentinel_rows"] == 1
    assert result["hard_negative_rows"] == 1
    assert result["result_class"] == "v3_sequence_outcome_corpus_exported"
    assert result["future_only_fault_count"] == 1

    positives = _read_csv(tmp_path / "run" / "positive_sequence_outcomes.csv")
    assert positives[0]["pair_id"] == "pair-1"
    assert positives[0]["source_kind"] == "v3_reset_source"
    assert positives[0]["preferred_fidelity_class"] == "current_model_proxy"
    assert positives[0]["wrong_fidelity_class"] == "current_model_fault"
    assert json.loads(positives[0]["preferred_fault_params_json"]) == {"cf_scale": 0.2}

    contrast = _read_csv(tmp_path / "run" / "contrast_rows.csv")
    assert [row["contrast_role"] for row in contrast] == [
        "normal",
        "positive_intervention",
        "hard_negative_action_only",
    ]
    assert contrast[1]["proof_positive"] == "True"
    assert contrast[2]["proof_positive"] == "False"


def test_classify_v3_sequence_outcome_corpus_artifact_before_balance():
    assert (
        classify_v3_sequence_outcome_corpus(
            positive_rows=1000,
            hard_negative_rows=1000,
            positive_sentinel_rows=0,
            positive_source_role_sentinel_rows=0,
            duplicate_positive_keys=0,
            missing_normal_matches=0,
            positive_rows_missing_v3_metadata=1,
            positive_rows_missing_fidelity_metadata=0,
            unique_positive_seeds=50,
            unique_positive_fault_family_pairs=30,
            max_positive_seed_dominance=0.05,
        )
        == "v3_sequence_outcome_corpus_artifact"
    )


def test_classify_v3_sequence_outcome_corpus_hard_negative_sparse():
    assert (
        classify_v3_sequence_outcome_corpus(
            positive_rows=1000,
            hard_negative_rows=999,
            positive_sentinel_rows=0,
            positive_source_role_sentinel_rows=0,
            duplicate_positive_keys=0,
            missing_normal_matches=0,
            positive_rows_missing_v3_metadata=0,
            positive_rows_missing_fidelity_metadata=0,
            unique_positive_seeds=50,
            unique_positive_fault_family_pairs=30,
            max_positive_seed_dominance=0.05,
        )
        == "v3_sequence_outcome_corpus_hard_negative_sparse"
    )
