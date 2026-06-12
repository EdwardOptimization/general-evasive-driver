from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path("scripts/feasibility_audit/c5prime_c1_tail_family_interface_synthesis_repricing.py")


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "c5prime_c1_tail_family_interface_synthesis_repricing",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_synthesize_decision_pivots_when_representation_alive_but_rare_family_fails():
    mod = _load_module()
    prereg = {
        "thresholds": {
            "min_priced_tail_mse_reduction": 0.15,
            "max_true_family_reconstruction_mse": 1e-12,
            "min_required_rare_validation_family_accuracy": 0.5,
        }
    }
    target_status = {
        "a3_c5prime_target_confirmed": True,
        "d1b_direction_positive_all_variants": True,
        "m3234_interface_pricing_positive": True,
        "m3234_priced_tail_mse_reduction": 0.369957,
    }
    representation = {
        "representationally_valid_if_family_known": True,
        "m3236_true_family_validation_reconstruction_mse": 0.0,
    }
    pretrain = {
        "quick_pretrain_passed": False,
        "worst_validation_family_accuracy": 0.0,
        "failed_gates": ["predicted_family_reconstruction_gate_passed"],
        "aggregate_validation_would_mislead": True,
    }

    decision = mod.synthesize_decision(prereg, target_status, representation, pretrain)

    assert decision["synthesis_decision"] == "pivot_to_family_selector_repricing"
    assert decision["next_training_admitted"] is False
    assert decision["controlled_rollout_design_admitted"] is False
    assert decision["c2_admitted"] is False


def test_summarize_pretrain_failure_marks_aggregate_metric_as_misleading():
    mod = _load_module()
    m3236 = {
        "decision": {"quick_pretrain_passed": False},
        "gates": {
            "all_passed": False,
            "validation_family_min_gate_passed": False,
            "predicted_family_reconstruction_gate_passed": False,
        },
        "metrics": {
            "accuracy_by_role": {"selection": 0.92, "validation": 0.76},
            "floors": {
                "validation_train_majority_accuracy": 0.53,
                "validation_centroid_accuracy": 0.44,
            },
            "validation_family_metrics": {
                "common": {"accuracy": 0.95, "frames": 100, "predicted_counts": {"common": 95}},
                "rare": {"accuracy": 0.0, "frames": 40, "predicted_counts": {"wrong": 40}},
            },
        },
    }

    summary = mod.summarize_pretrain_failure(m3236)

    assert summary["aggregate_validation_would_mislead"] is True
    assert summary["worst_validation_family"] == "rare"
