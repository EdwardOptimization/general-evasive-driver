from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path("scripts/feasibility_audit/c5prime_c1_admission_interface_pricing.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("c5prime_c1_admission_interface_pricing", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_family_coverage_reports_missing_support_and_supported_library():
    mod = _load_module()
    rows = [
        {"bc_role": "train", "oracle_by": "structured:brake_steer_+0.4"},
        {"bc_role": "validation", "oracle_by": "structured:brake_steer_+0.4"},
        {"bc_role": "validation", "oracle_by": "structured:coast_steer_-0.7"},
    ]

    coverage = mod.family_coverage(rows)

    assert coverage["heldout_family_train_coverage"] == 0.5
    assert coverage["missing_train_support_for_heldout"] == ["structured:coast_steer_-0.7"]
    assert coverage["all_families_supported_by_structured_library"] is True


def test_tail_frame_summary_uses_reveal_step_by_row():
    mod = _load_module()
    prereg = {
        "selected_rows": [
            {
                "row_id": "r0",
                "bc_role": "validation",
                "oracle_by": "structured:full_brake",
                "reveal_step": 3,
            }
        ]
    }
    summary = {
        "demo_outcomes": {
            "r0": {
                "role": "validation",
                "steps": 10,
            }
        }
    }

    out = mod.tail_frame_summary(prereg, summary)

    assert out["prefix_frames"] == 3
    assert out["tail_frames"] == 7
    assert out["tail_frame_share"] == 0.7
    assert out["tail_frames_by_family"] == {"structured:full_brake": 7}


def test_interface_price_positive_when_tail_reduction_and_coverage_pass():
    mod = _load_module()
    prereg = {
        "thresholds": {
            "direct_action_mse_gate": 0.12,
            "min_tail_mse_reduction": 0.15,
            "min_heldout_family_train_coverage": 1.0,
        }
    }
    m3228 = {"bc_training": {"validation_action_mse": 0.23}}
    m3232 = {"bc_training": {"validation_action_mse": 0.29}}
    m3229 = {"recomputed_mse": {"by_segment_frame_mse": {"validation:tail": 0.37}}}
    m3233 = {"decision": {"target_still_priced": True, "local_branch_pivots": True}}
    coverage = {
        "heldout_family_train_coverage": 1.0,
        "missing_train_support_for_heldout": [],
        "unsupported_structured_families": [],
        "all_families_supported_by_structured_library": True,
    }

    price = mod.build_interface_price(prereg, m3228, m3229, m3232, m3233, coverage)

    assert price["positive"] is True
    assert price["verdict"] == "interface_pricing_positive"
    assert price["tail_interface_oracle_anchor"]["priced_tail_mse_reduction"] == 0.37
