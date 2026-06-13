from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase4_e2prime_chrono_two_regime_hardened as e2p  # noqa: E402


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
    for unit in e2p._selection_units(prereg):
        name = unit["candidate"]["name"]
        group = unit["candidate"]["group"]
        success = name in {seeker_winner, fixed_winner, oracle_winner}
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


def _selections(prereg: dict, *, seeker: dict, fixed: dict, oracle: dict) -> dict:
    return {
        f"{variant}|{float(reveal):g}": {
            "best_seeker": seeker["name"],
            "best_fixed": fixed["name"],
            "best_floor": seeker["name"],
            "oracle_by_mu": {f"{float(mu):g}": oracle["name"] for mu in prereg["mu_points"]},
        }
        for variant in prereg["chrono_variants"]
        for reveal in prereg["clean_reveal_tiers_m"]
    }


def test_preregistration_freezes_e2prime_scope_and_expected_rows() -> None:
    prereg = e2p.build_preregistration()
    seeker = _candidate(prereg, group="seeker")
    fixed = _candidate(prereg, group="fixed")
    oracle = _candidate(prereg, group="oracle")
    selections = _selections(prereg, seeker=seeker, fixed=fixed, oracle=oracle)

    assert prereg["frozen_before_any_e2prime_rollout"] is True
    assert prereg["chrono_variants"] == ["sedan_tmeasy", "uazbus_tmeasy"]
    assert prereg["selection_seeds"] == [0]
    assert prereg["validation_seeds"] == list(range(30))
    assert prereg["tight_reveal_tiers_m"] == [9.5, 12.0]
    assert prereg["min_validation_seeds_per_cell"] == 30
    assert prereg["seed_streams"]["selection_namespace"] == "selection"
    assert prereg["seed_streams"]["validation_namespace"] == "validation"
    assert len(prereg["controller_candidates"]) == 14

    selection_units = e2p._selection_units(prereg)
    validation_units = e2p._validation_units(prereg, selections)
    assert len(selection_units) == 560
    assert len(validation_units) == 5760
    assert {unit["seed"] for unit in selection_units}.isdisjoint({unit["seed"] for unit in validation_units})

    quick = e2p._quick_prereg(prereg)
    assert len(e2p._selection_units(quick)) == 28
    assert len(e2p._validation_units(quick, _selections(quick, seeker=seeker, fixed=fixed, oracle=oracle))) == 16


def test_select_arms_uses_clean_selection_rows_by_variant_and_reveal() -> None:
    prereg = e2p.build_preregistration()
    seeker = _candidate(prereg, group="seeker", contains="r6000")
    fixed = _candidate(prereg, group="fixed", contains="fixedspeed_v7.5")
    oracle = _candidate(prereg, group="oracle", contains="+0.5")
    rows = _selection_rows_for_prereg(
        prereg,
        seeker_winner=seeker["name"],
        fixed_winner=fixed["name"],
        oracle_winner=oracle["name"],
    )

    selections = e2p.select_arms(rows, prereg)

    for variant in prereg["chrono_variants"]:
        for reveal in prereg["clean_reveal_tiers_m"]:
            selected = selections[f"{variant}|{float(reveal):g}"]
            assert selected["best_seeker"] == seeker["name"]
            assert selected["best_fixed"] == fixed["name"]
            assert selected["best_floor"] == seeker["name"]
            assert set(selected["oracle_by_mu"].values()) == {oracle["name"]}


def test_summarize_panel_confirms_flip_only_when_two_tight_cells_on_two_variants_pass() -> None:
    prereg = e2p.build_preregistration()
    seeker = _candidate(prereg, group="seeker")
    fixed = _candidate(prereg, group="fixed")
    oracle = _candidate(prereg, group="oracle")
    selections = _selections(prereg, seeker=seeker, fixed=fixed, oracle=oracle)
    rows = _selection_rows_for_prereg(
        prereg,
        seeker_winner=seeker["name"],
        fixed_winner=fixed["name"],
        oracle_winner=oracle["name"],
    )
    tight = {float(reveal) for reveal in prereg["tight_reveal_tiers_m"]}
    for unit in e2p._validation_units(prereg, selections):
        is_tight_clean = unit["cell"]["cell_id"] == "clean" and float(unit["reveal"]) in tight
        success = is_tight_clean and unit["logical_arm"] == "oracle"
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
                "success": "True" if success else "False",
                "score": "1.0",
                "reset_obs_finite": "True",
                "variant_match": "True",
            }
        )

    summary = e2p.summarize_panel(
        rows,
        prereg,
        selections=selections,
        calibration={variant: {"tau": 0.08} for variant in prereg["chrono_variants"]},
        elapsed_s=1.0,
        mode="full",
        rows_csv=e2p.ROWS_FULL_CSV,
        metrics_csv=e2p.METRICS_FULL_CSV,
        require_full_power=True,
    )

    assert summary["protocol_gates"]["all_passed"] is True
    assert summary["decision"]["e2prime_full_verdict"] == "e2prime_flip_confirmed"
    assert summary["decision"]["variants_confirming_flip"] == ["sedan_tmeasy", "uazbus_tmeasy"]
    assert summary["decision"]["tight_positive_cell_count"] == 4
    assert summary["decision"]["track_f_admitted"] is False


def test_summarize_panel_fails_incomplete_validation_rows_and_keeps_track_f_blocked() -> None:
    prereg = e2p.build_preregistration()
    seeker = _candidate(prereg, group="seeker")
    fixed = _candidate(prereg, group="fixed")
    oracle = _candidate(prereg, group="oracle")
    selections = _selections(prereg, seeker=seeker, fixed=fixed, oracle=oracle)
    rows = _selection_rows_for_prereg(
        prereg,
        seeker_winner=seeker["name"],
        fixed_winner=fixed["name"],
        oracle_winner=oracle["name"],
    )

    summary = e2p.summarize_panel(
        rows,
        prereg,
        selections=selections,
        calibration={variant: {"tau": 0.08} for variant in prereg["chrono_variants"]},
        elapsed_s=1.0,
        mode="full",
        rows_csv=e2p.ROWS_FULL_CSV,
        metrics_csv=e2p.METRICS_FULL_CSV,
        require_full_power=True,
    )

    assert summary["protocol_gates"]["validation_rows_complete"] is False
    assert summary["protocol_gates"]["all_passed"] is False
    assert summary["decision"]["e2prime_full_verdict"] == "e2prime_flip_not_confirmed"
    assert summary["decision"]["track_f_admitted"] is False
