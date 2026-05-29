import argparse

import numpy as np

from autodrift.extreme_dynamics_scenario_corpus import FaultSpec
from autodrift.warmup_latched_config_smoke import (
    bucket,
    classify_warmup_smoke_result,
    fault_evidence_steps,
    parse_int_list,
    reveal_bucket_key,
    source_diversity,
    warmup_gate_clearance_margin_band,
    warmup_gate_diagnostics,
    warmup_gate_source_stratum_metrics,
    warmup_gate_strata_summary,
)


def test_parse_int_list_rejects_empty_and_nonpositive():
    assert parse_int_list("48,56") == (48, 56)
    for raw in ("", "4,0"):
        try:
            parse_int_list(raw)
        except argparse.ArgumentTypeError:
            pass
        else:
            raise AssertionError("expected argparse.ArgumentTypeError")


def test_reveal_bucket_key_uses_coarse_current_state():
    obs = np.zeros(72, dtype=np.float32)
    obs[0] = 0.8
    obs[2] = 0.2
    obs[5] = 0.12
    info = {"obstacle_distance": 14.2, "obstacle_lateral_offset": -0.6}

    key = reveal_bucket_key(obs, info)

    assert key.startswith("vx8|")
    assert "ox3" in key
    assert "oy-2" in key


def test_fault_evidence_steps_clamps_pre_activation():
    fault = FaultSpec(
        name="late",
        family="test",
        severity="x",
        activation_step=20,
        params={},
    )

    assert fault_evidence_steps(fault, 12) == 0
    assert fault_evidence_steps(fault, 28) == 8


def test_source_diversity_counts_reveal_buckets():
    rows = [
        {"seed": 1, "capability_pair": "a->b", "preferred_reveal_bucket": "x", "preferred_fault_family": "a", "wrong_fault_family": "b"},
        {"seed": 2, "capability_pair": "a->b", "preferred_reveal_bucket": "y", "preferred_fault_family": "a", "wrong_fault_family": "b"},
        {"seed": 2, "capability_pair": "c->d", "preferred_reveal_bucket": "y", "preferred_fault_family": "c", "wrong_fault_family": "d"},
    ]

    summary = source_diversity(rows)

    assert summary["unique_source_seeds"] == 2
    assert summary["unique_capability_pairs"] == 2
    assert summary["unique_reveal_buckets"] == 2


def test_classify_warmup_smoke_result_requires_structural_thresholds():
    assert (
        classify_warmup_smoke_result(
            source_rows=512,
            matched_or_bucketed_rows=160,
            unique_source_seeds=24,
            unique_capability_pairs=8,
            unique_reveal_buckets=8,
            finite_metric_rows=512,
            actor_parameters_changed=False,
        )
        == "warmup_latched_structural_pass"
    )
    assert (
        classify_warmup_smoke_result(
            source_rows=512,
            matched_or_bucketed_rows=159,
            unique_source_seeds=24,
            unique_capability_pairs=8,
            unique_reveal_buckets=8,
            finite_metric_rows=512,
            actor_parameters_changed=False,
        )
        == "warmup_latched_structural_sparse"
    )


def test_warmup_gate_diagnostics_counts_visible_evidence_rows():
    rows = [
        {
            "preferred_warmup_gate_visible_steps": 3,
            "wrong_warmup_gate_visible_steps": 0,
            "preferred_warmup_gate_collision": False,
            "wrong_warmup_gate_collision": False,
            "preferred_warmup_gate_passed": True,
            "wrong_warmup_gate_passed": False,
            "warmup_response_history_l2": 0.12,
            "warmup_action_history_l2": 0.0,
            "warmup_context_history_l2": 0.2,
            "preferred_warmup_gate_clearance_margin": 1.0,
            "wrong_warmup_gate_clearance_margin": 0.8,
        },
        {
            "preferred_warmup_gate_visible_steps": 0,
            "wrong_warmup_gate_visible_steps": 0,
            "preferred_warmup_gate_collision": True,
            "wrong_warmup_gate_collision": False,
            "preferred_warmup_gate_passed": False,
            "wrong_warmup_gate_passed": False,
            "warmup_response_history_l2": 0.0,
            "warmup_action_history_l2": 0.0,
            "warmup_context_history_l2": 0.0,
            "preferred_warmup_gate_clearance_margin": -0.1,
            "wrong_warmup_gate_clearance_margin": 0.0,
        },
    ]

    summary = warmup_gate_diagnostics(rows)

    assert summary["rows"] == 2
    assert summary["warmup_gate_visible_rows"] == 1
    assert summary["warmup_evidence_rows"] == 1
    assert summary["warmup_gate_collision_rows"] == 1
    assert summary["warmup_gate_collision_share"] == 0.5
    assert summary["preferred_warmup_gate_passed_rows"] == 1
    assert summary["warmup_response_history_l2"]["max"] == 0.12


def test_warmup_gate_source_strata_summary_counts_matched_rows():
    metrics = {
        "preferred_warmup_gate_collision": False,
        "wrong_warmup_gate_collision": False,
        "preferred_warmup_gate_clearance_margin": 0.4,
        "wrong_warmup_gate_clearance_margin": 0.5,
    }
    collision_metrics = {
        **metrics,
        "preferred_warmup_gate_collision": True,
        "preferred_warmup_gate_clearance_margin": -0.1,
    }
    rows = [
        {
            "seed": 1,
            "capability_pair": "a->b",
            "preferred_reveal_bucket": "x",
            "matched_current_pass": True,
            "bucketed_current_pass": False,
            "matched_or_bucketed_reveal_pass": True,
            "warmup_response_history_l2": 0.1,
            "warmup_action_history_l2": 0.01,
            **warmup_gate_source_stratum_metrics(metrics),
        },
        {
            "seed": 2,
            "capability_pair": "a->b",
            "preferred_reveal_bucket": "y",
            "matched_current_pass": False,
            "bucketed_current_pass": False,
            "matched_or_bucketed_reveal_pass": False,
            "warmup_response_history_l2": 0.2,
            "warmup_action_history_l2": 0.02,
            **warmup_gate_source_stratum_metrics(collision_metrics),
        },
    ]

    summary = {row["warmup_gate_collision_stratum"]: row for row in warmup_gate_strata_summary(rows)}

    assert warmup_gate_clearance_margin_band(0.4) == "clear_0p25_1p00"
    assert summary["clear"]["matched_or_bucketed_rows"] == 1
    assert summary["collision"]["rows"] == 1
