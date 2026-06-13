from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase4_e2_chrono_two_regime_full as e2_full  # noqa: E402


def _candidate(prereg: dict, *, group: str, contains: str | None = None) -> dict:
    for candidate in prereg["controller_candidates"]:
        if candidate["group"] != group:
            continue
        if contains is not None and contains not in candidate["name"]:
            continue
        return candidate
    raise AssertionError(f"missing candidate group={group!r} contains={contains!r}")


def _selection_rows_for_prereg(
    prereg: dict,
    *,
    seeker_winner: str,
    fixed_winner: str,
    oracle_winner: str,
) -> list[dict[str, str]]:
    rows = []
    for unit in e2_full._selection_units(prereg):
        name = unit["candidate"]["name"]
        group = unit["candidate"]["group"]
        success = (
            name == seeker_winner
            or name == fixed_winner
            or name == oracle_winner
        )
        score = 100.0 if success else 1.0
        rows.append(
            {
                "phase": "selection",
                "variant": unit["variant"],
                "cell_id": unit["cell"]["cell_id"],
                "reveal_m": str(unit["reveal"]),
                "mu": str(unit["mu"]),
                "seed": str(unit["seed"]),
                "logical_arm": group,
                "candidate_group": group,
                "candidate_name": name,
                "success": "True" if success else "False",
                "score": str(score),
                "reset_obs_finite": "True",
                "variant_match": "True",
            }
        )
    return rows


def test_full_preregistration_freezes_sedan_scope_and_expected_rows() -> None:
    prereg = e2_full.build_preregistration()
    seeker = _candidate(prereg, group="seeker")
    fixed = _candidate(prereg, group="fixed")
    oracle = _candidate(prereg, group="oracle")
    selections = {
        "sedan_tmeasy|9.5": {
            "best_seeker": seeker["name"],
            "best_fixed": fixed["name"],
            "best_floor": seeker["name"],
            "oracle_by_mu": {f"{float(mu):g}": oracle["name"] for mu in prereg["mu_points"]},
        }
    }

    assert prereg["frozen_before_any_e2_full_rollout"] is True
    assert prereg["chrono_variants"] == ["sedan_tmeasy"]
    assert prereg["selection_seeds"] == [0]
    assert prereg["validation_seeds"] == [0, 1]
    assert prereg["seed_streams"]["selection_namespace"] == "selection"
    assert prereg["seed_streams"]["validation_namespace"] == "validation"
    assert len(prereg["controller_candidates"]) == 14
    selection_units = e2_full._selection_units(prereg)
    assert len(selection_units) == 280

    selections = {
        f"sedan_tmeasy|{float(reveal):g}": selections["sedan_tmeasy|9.5"]
        for reveal in prereg["clean_reveal_tiers_m"]
    }
    validation_units = e2_full._validation_units(prereg, selections)
    assert len(validation_units) == 192
    assert {unit["seed"] for unit in selection_units}.isdisjoint(
        {unit["seed"] for unit in validation_units}
    )


def test_select_arms_uses_clean_selection_rows_only() -> None:
    prereg = e2_full.build_preregistration()
    seeker = _candidate(prereg, group="seeker", contains="r6000")
    fixed = _candidate(prereg, group="fixed", contains="fixedspeed_v7.5")
    oracle = _candidate(prereg, group="oracle", contains="+0.5")
    rows = _selection_rows_for_prereg(
        prereg,
        seeker_winner=seeker["name"],
        fixed_winner=fixed["name"],
        oracle_winner=oracle["name"],
    )

    selections = e2_full.select_arms(rows, prereg)

    for reveal in prereg["clean_reveal_tiers_m"]:
        selected = selections[f"sedan_tmeasy|{float(reveal):g}"]
        assert selected["best_seeker"] == seeker["name"]
        assert selected["best_fixed"] == fixed["name"]
        assert selected["best_floor"] == seeker["name"]
        assert set(selected["oracle_by_mu"].values()) == {oracle["name"]}


def test_summarize_full_applies_clean_positive_rule_and_keeps_track_f_blocked() -> None:
    prereg = e2_full.build_preregistration()
    seeker = _candidate(prereg, group="seeker")
    fixed = _candidate(prereg, group="fixed")
    oracle = _candidate(prereg, group="oracle")
    selections = {
        f"sedan_tmeasy|{float(reveal):g}": {
            "best_seeker": seeker["name"],
            "best_fixed": fixed["name"],
            "best_floor": seeker["name"],
            "oracle_by_mu": {f"{float(mu):g}": oracle["name"] for mu in prereg["mu_points"]},
        }
        for reveal in prereg["clean_reveal_tiers_m"]
    }
    rows = _selection_rows_for_prereg(
        prereg,
        seeker_winner=seeker["name"],
        fixed_winner=fixed["name"],
        oracle_winner=oracle["name"],
    )
    positive_reveal = prereg["clean_reveal_tiers_m"][0]
    for unit in e2_full._validation_units(prereg, selections):
        is_positive_cell = (
            unit["cell"]["cell_id"] == "clean"
            and float(unit["reveal"]) == float(positive_reveal)
            and unit["logical_arm"] == "oracle"
        )
        is_floor_positive_cell = (
            unit["cell"]["cell_id"] == "clean"
            and float(unit["reveal"]) == float(positive_reveal)
            and unit["logical_arm"] == "best_floor"
        )
        success = is_positive_cell or (
            unit["cell"]["cell_id"] == "clean"
            and float(unit["reveal"]) != float(positive_reveal)
            and unit["logical_arm"] in {"oracle", "best_floor"}
        )
        rows.append(
            {
                "phase": "validation",
                "variant": unit["variant"],
                "cell_id": unit["cell"]["cell_id"],
                "reveal_m": str(unit["reveal"]),
                "mu": str(unit["mu"]),
                "seed": str(unit["seed"]),
                "logical_arm": unit["logical_arm"],
                "candidate_group": unit["candidate"]["group"],
                "candidate_name": unit["candidate"]["name"],
                "success": "False" if is_floor_positive_cell else ("True" if success else "False"),
                "score": "1.0",
                "reset_obs_finite": "True",
                "variant_match": "True",
            }
        )

    summary = e2_full.summarize_full(
        rows,
        prereg,
        selections=selections,
        calibration={"sedan_tmeasy": {"tau": 0.08}},
        elapsed_s=1.0,
    )

    assert summary["protocol_gates"]["all_passed"] is True
    assert summary["decision"]["e2_full_verdict"] == "chrono_clean_belief_value_positive"
    assert summary["decision"]["qualifying_clean_reveals_m"] == [float(positive_reveal)]
    assert summary["decision"]["track_f_admitted"] is False
    assert summary["validation_row_count"] == summary["validation_row_count_expected"]


def test_summarize_full_fails_incomplete_validation_rows() -> None:
    prereg = e2_full.build_preregistration()
    seeker = _candidate(prereg, group="seeker")
    fixed = _candidate(prereg, group="fixed")
    oracle = _candidate(prereg, group="oracle")
    selections = {
        f"sedan_tmeasy|{float(reveal):g}": {
            "best_seeker": seeker["name"],
            "best_fixed": fixed["name"],
            "best_floor": seeker["name"],
            "oracle_by_mu": {f"{float(mu):g}": oracle["name"] for mu in prereg["mu_points"]},
        }
        for reveal in prereg["clean_reveal_tiers_m"]
    }
    rows = _selection_rows_for_prereg(
        prereg,
        seeker_winner=seeker["name"],
        fixed_winner=fixed["name"],
        oracle_winner=oracle["name"],
    )

    summary = e2_full.summarize_full(
        rows,
        prereg,
        selections=selections,
        calibration={"sedan_tmeasy": {"tau": 0.08}},
        elapsed_s=1.0,
    )

    assert summary["protocol_gates"]["validation_rows_complete"] is False
    assert summary["protocol_gates"]["all_passed"] is False
    assert summary["decision"]["e2_full_verdict"] == "chrono_clean_threshold_seeker_null_not_rejected"
