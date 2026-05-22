import pandas as pd

from autodrift.critical_key_replay_guard import derive_protected_cases, evaluate_protected_cases


def test_derive_protected_cases_from_reference_rows():
    reference = pd.DataFrame(
        [
            {
                "seed": 9944,
                "target_obstacle_distance": 11.0,
                "relocated_obstacle_body_y": -1.0,
                "relocated_obstacle_half_width": 0.9,
                "nominal_step": 28,
                "perturbed_step": 28,
                "nominal_accepted_outcome_sensitive": False,
                "perturbed_accepted_outcome_sensitive": True,
                "perturbed_normal_margin": 0.076748,
                "perturbed_wrong_history_margin": 0.071552,
                "perturbed_margin_gap": 0.005196,
            }
        ]
    )

    cases = derive_protected_cases([reference], case_keys={"9944|perturbed|28|28"})

    assert len(cases) == 1
    assert cases.iloc[0]["key"] == "9944|perturbed|28|28"
    assert cases.iloc[0]["source_condition"] == "perturbed"
    assert cases.iloc[0]["reference_margin_gap"] == 0.005196


def test_evaluate_protected_cases_detects_threshold_loss():
    protected_cases = pd.DataFrame(
        [
            {
                "seed": 9944,
                "source_condition": "perturbed",
                "source_step": 28,
                "paired_step": 28,
                "target_obstacle_distance": 11.0,
                "relocated_obstacle_body_y": -1.0,
                "relocated_obstacle_half_width": 0.9,
                "reference_normal_margin": 0.076748,
                "reference_wrong_history_margin": 0.071552,
                "reference_margin_gap": 0.005196,
            }
        ]
    )
    candidates = pd.DataFrame(
        [
            {
                "seed": 9944,
                "target_obstacle_distance": 11.0,
                "relocated_obstacle_body_y": -1.0,
                "relocated_obstacle_half_width": 0.9,
                "nominal_step": 28,
                "perturbed_step": 28,
                "perturbed_accepted_outcome_sensitive": False,
                "perturbed_normal_success": True,
                "perturbed_normal_margin": 0.075643,
                "perturbed_wrong_history_margin": 0.070968,
                "perturbed_margin_gap": 0.004675,
            }
        ]
    )

    result = evaluate_protected_cases(candidates, protected_cases, policy="m139")

    assert len(result) == 1
    assert not bool(result.iloc[0]["accepted"])
    assert result.iloc[0]["found_rows"] == 1
    assert result.iloc[0]["margin_gap"] == 0.004675
    assert result.iloc[0]["margin_gap_delta_vs_reference"] < 0.0
