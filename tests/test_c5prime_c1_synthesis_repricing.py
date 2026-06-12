from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path("scripts/feasibility_audit/c5prime_c1_synthesis_repricing.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("c5prime_c1_synthesis_repricing", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _attempt(gate_passed: bool, mse: float, zero: float) -> dict:
    return {
        "bc_training": {
            "validation_action_mse": mse,
            "validation_zero_action_baseline_mse": zero,
            "validation_mse_gate_passed": gate_passed,
            "validation_bc_success_rate_context": 0.5,
            "validation_bc_rollouts": [
                {"outcome_bucket": "success_obstacle_pass"},
                {"outcome_bucket": "collision_failure"},
            ],
            "final": {"best_epoch": 4, "best_selection_mse": 0.03, "best_train_mse": 0.05},
        },
        "demo_frame_counts": {"train": 10, "selection": 4, "validation": 4},
        "gates": {
            "demo_replay_all_success": True,
            "checkpoint_exists": True,
            "dataset_exists": True,
            "all_passed": gate_passed,
        },
        "quick_mode": False,
        "role_counts": {"train": 2, "selection": 1, "validation": 1},
        "selected_rows": [{"row_id": "r0"}],
    }


def test_synthesis_pivots_after_two_action_mse_failures_with_healthy_artifacts():
    mod = _load_module()
    prereg = {
        "thresholds": {
            "validation_action_mse_gate": 0.12,
            "max_action_mse_gate_failures_before_synthesis": 2,
            "minimum_validation_mse_improvement_for_local_repair": 0.03,
        }
    }
    attempts = [
        mod.summarize_attempt(
            milestone="M3228",
            mode="full",
            revision="v1",
            summary=_attempt(False, 0.23, 0.50),
            action_mse_threshold=0.12,
        ),
        mod.summarize_attempt(
            milestone="M3232",
            mode="quick",
            revision="v2",
            summary=_attempt(False, 0.29, 0.56),
            action_mse_threshold=0.12,
        ),
    ]
    decision = mod.synthesize_decision(
        prereg,
        attempts,
        {"diagnosis_flags": ["tail_action_generalization_dominates"]},
        {"c5prime_target_confirmed": True},
        {"d1b_direction_positive_all_variants": True},
    )

    assert decision["synthesis_decision"] == "pivot"
    assert decision["c1_status"] == "open"
    assert decision["c2_admitted"] is False
    assert decision["another_local_mlp_bc_repair_admitted"] is False
    assert decision["validation_mse_improvement_m3228_minus_m3232"] < 0.0


def test_summarize_localization_reports_tail_and_dominant_channel():
    mod = _load_module()
    summary = mod.summarize_localization(
        {
            "diagnosis_flags": ["tail_action_generalization_dominates"],
            "recomputed_mse": {
                "by_segment_frame_mse": {
                    "validation:prefix": 0.02,
                    "validation:tail": 0.30,
                },
                "by_action_channel_frame_mse": {
                    "steer": 0.03,
                    "throttle": 0.01,
                    "brake": 0.20,
                },
            },
        }
    )

    assert summary["validation_tail_prefix_ratio"] == 15.0
    assert summary["dominant_action_channel"] == "brake"
    assert summary["dominant_action_channel_share"] > 0.8
