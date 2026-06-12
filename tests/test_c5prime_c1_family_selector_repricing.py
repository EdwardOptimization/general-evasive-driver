from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path("scripts/feasibility_audit/c5prime_c1_family_selector_repricing.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("c5prime_c1_family_selector_repricing", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_row_one_nn_predictions_use_train_rows_only():
    mod = _load_module()
    features = np.asarray(
        [
            [0.0, 0.0],
            [10.0, 0.0],
            [9.0, 0.0],
            [9.1, 0.0],
        ],
        dtype=np.float32,
    )
    row_family = np.asarray([0, 1, 0, 0], dtype=np.int64)
    row_role = np.asarray([0, 0, 1, 2], dtype=np.int64)

    pred, _distances, nearest = mod.row_one_nn_predictions(features, row_family, row_role)

    assert pred[2] == 1
    assert pred[3] == 1
    assert nearest[2] == 1
    assert nearest[3] == 1


def test_add_gate_results_rejects_row_selector_when_required_rare_margin_is_negative():
    mod = _load_module()
    selector = {
        "name": "row_1nn_mean_std_first_last_z",
        "kind": "row_1nn",
        "accuracy_by_role": {"validation": 0.85},
        "validation_predicted_family_reconstruction_mse": 0.05,
        "required_rare_validation_families": {
            "structured:coast_steer_-0.7": {
                "frame_accuracy": 1.0,
                "row_accuracy": 1.0,
                "margin_min": -0.25,
            }
        },
    }
    thresholds = {
        "min_validation_accuracy_over_majority_floor": 0.15,
        "min_required_rare_validation_family_accuracy": 0.5,
        "min_required_rare_row_accuracy": 1.0,
        "min_required_rare_margin": 0.0,
        "max_predicted_family_validation_reconstruction_mse": 0.1,
    }

    enriched = mod.add_gate_results(selector, floor_accuracy=0.60, thresholds=thresholds)

    assert enriched["gates"]["validation_accuracy_over_floor_gate_passed"] is True
    assert enriched["gates"]["required_rare_frame_accuracy_gate_passed"] is True
    assert enriched["gates"]["predicted_family_reconstruction_gate_passed"] is True
    assert enriched["gates"]["required_rare_row_gate_passed"] is False
    assert enriched["gates"]["all_passed"] is False


def test_synthesize_decision_blocks_training_when_no_selector_is_admissible():
    mod = _load_module()
    prereg = {}
    m3237 = {
        "decision": {
            "target_still_priced": True,
            "representation_alive_if_family_known": True,
        }
    }
    evaluated = {
        "admissible_selectors": [],
        "best_by_validation_mse": {
            "name": "row_1nn_mean_std_first_last_z",
            "validation_accuracy": 0.803119,
            "validation_predicted_family_reconstruction_mse": 0.268415,
            "gates": {
                "all_passed": False,
                "required_rare_frame_accuracy_gate_passed": False,
            },
        },
    }

    decision = mod.synthesize_decision(prereg, m3237, evaluated)

    assert decision["synthesis_decision"] == "family_selector_repricing_negative"
    assert decision["c1_status"] == "blocked_pending_pi_or_new_interface_pricing"
    assert decision["next_training_admitted"] is False
    assert decision["c2_admitted"] is False
