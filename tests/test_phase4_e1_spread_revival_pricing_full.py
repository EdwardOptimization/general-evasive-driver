from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase4_e1_spread_revival_pricing_full as e1_full  # noqa: E402


def test_full_preregistration_freezes_disjoint_same_instance_pairs() -> None:
    prereg = e1_full.build_preregistration()

    assert prereg["frozen_before_any_e1_full_run"] is True
    assert prereg["chrono_vehicle_variants"] == ["sedan_tmeasy", "bmw_e90_tmeasy", "uazbus_tmeasy"]
    assert len(prereg["row_pairs"]) == 6
    assert "payload_position_or_cg_height" in prereg["blocked_by_e0_without_new_connector"]

    selection_ids = {pair["selection_row"]["row_id"] for pair in prereg["row_pairs"]}
    validation_ids = {pair["validation_row"]["row_id"] for pair in prereg["row_pairs"]}
    assert selection_ids.isdisjoint(validation_ids)
    assert all(pair["selection_row"]["instance"] == pair["validation_row"]["instance"] for pair in prereg["row_pairs"])
    assert all(pair["selection_row"]["level"] == pair["validation_row"]["level"] for pair in prereg["row_pairs"])


def test_choose_grids_from_selection_uses_global_and_pair_scores() -> None:
    prereg = {
        "chrono_vehicle_variants": ["sedan_tmeasy", "bmw_e90_tmeasy"],
        "row_pairs": [{"pair_id": "S1-inst01-pair1"}, {"pair_id": "S2-inst02-pair1"}],
        "full_grid_values": [[1.0, 1.0, 1.0], [1.8, 1.0, 1.0]],
    }
    rows = []
    scores = {
        ("sedan_tmeasy", "S1-inst01-pair1", (1.0, 1.0, 1.0)): 1.0,
        ("sedan_tmeasy", "S1-inst01-pair1", (1.8, 1.0, 1.0)): 5.0,
        ("sedan_tmeasy", "S2-inst02-pair1", (1.0, 1.0, 1.0)): 4.0,
        ("sedan_tmeasy", "S2-inst02-pair1", (1.8, 1.0, 1.0)): 1.0,
        ("bmw_e90_tmeasy", "S1-inst01-pair1", (1.0, 1.0, 1.0)): 4.0,
        ("bmw_e90_tmeasy", "S1-inst01-pair1", (1.8, 1.0, 1.0)): 1.0,
        ("bmw_e90_tmeasy", "S2-inst02-pair1", (1.0, 1.0, 1.0)): 4.0,
        ("bmw_e90_tmeasy", "S2-inst02-pair1", (1.8, 1.0, 1.0)): 1.0,
    }
    for (variant, pair_id, grid), score in scores.items():
        rows.append(
            {
                "role": "selection",
                "arm": "fixed_star_selection_candidate",
                "variant": variant,
                "pair_id": pair_id,
                "row_id": "selection-row",
                "grid": str(grid),
                "score": str(score),
            }
        )

    fixed, pertuned, _summary = e1_full.choose_grids_from_selection(rows, prereg)

    assert fixed == (1.0, 1.0, 1.0)
    assert pertuned[("sedan_tmeasy", "S1-inst01-pair1")] == (1.8, 1.0, 1.0)
    assert pertuned[("sedan_tmeasy", "S2-inst02-pair1")] == (1.0, 1.0, 1.0)


def test_summarize_full_applies_two_variant_positive_rule() -> None:
    prereg = e1_full.build_preregistration()
    rows = []
    grid = tuple(prereg["full_grid_values"][0])
    for variant in prereg["chrono_vehicle_variants"]:
        for pair in prereg["row_pairs"]:
            for candidate_grid in prereg["full_grid_values"]:
                rows.append(
                    {
                        "role": "selection",
                        "arm": "fixed_star_selection_candidate",
                        "variant": variant,
                        "pair_id": pair["pair_id"],
                        "row_id": pair["selection_row"]["row_id"],
                        "grid": str(tuple(candidate_grid)),
                        "score": "1.0",
                    }
                )
            positive_variant = variant in {"sedan_tmeasy", "bmw_e90_tmeasy"}
            outcomes = {
                "fixed_star": "collision",
                "v4_rls": "collision",
                "v4_pertuned": "success" if positive_variant else "collision",
                "native_oracle": "success" if positive_variant else "collision",
            }
            for arm, outcome in outcomes.items():
                rows.append(
                    {
                        "role": "validation",
                        "variant": variant,
                        "pair_id": pair["pair_id"],
                        "row_id": pair["validation_row"]["row_id"],
                        "arm": arm,
                        "chrono_outcome": outcome,
                        "reset_obs_finite": "True",
                        "variant_match": "True",
                    }
                )

    fixed, _pertuned, selection_summary = e1_full.choose_grids_from_selection(rows, prereg)
    summary = e1_full.summarize_full(rows, prereg, fixed_grid=fixed, selection_summary=selection_summary)

    assert summary["protocol_gates"]["all_passed"] is True
    assert summary["decision"]["e1_full_verdict"] == "e1_spread_revival_positive"
    assert set(summary["decision"]["qualifying_variants"]) == {"sedan_tmeasy", "bmw_e90_tmeasy"}
    assert summary["pooled"]["primary_prize_pertuned_minus_fixed_star"]["n_pairs"] == 18
