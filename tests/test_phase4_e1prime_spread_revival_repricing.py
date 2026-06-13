from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase4_e1prime_spread_revival_repricing as e1prime  # noqa: E402


def _fake_chrono_result(variant: str) -> dict:
    return {
        "outcome": "success",
        "steps": 1,
        "terminated": True,
        "truncated": False,
        "backend_status": "terminated",
        "termination_reason": "obstacle_pass",
        "completion_reason": "obstacle_pass",
        "collision": False,
        "obstacle_completed": True,
        "obstacle_visible_step": 0,
        "min_clearance_margin": 1.0,
        "trace_signature": "fake",
        "reset_obs_finite": True,
        "variant_match": True,
        "backend_info": {
            "backend_id": "fake",
            "chrono_vehicle_variant": variant,
            "chrono_vehicle_model": "fake",
            "chrono_tire_model": "fake",
        },
    }


class _DummyChronoClient:
    def __init__(self, *args, **kwargs) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def _small_selection_prereg(pair_count: int = 2, grid_count: int = 2) -> dict:
    prereg = e1prime.build_preregistration()
    prereg = dict(prereg)
    prereg["chrono_vehicle_variants"] = ["sedan_tmeasy"]
    prereg["row_pairs"] = list(prereg["row_pairs"][:pair_count])
    prereg["full_grid_values"] = list(prereg["full_grid_values"][:grid_count])
    return prereg


def test_full_preregistration_freezes_disjoint_same_instance_pairs() -> None:
    prereg = e1prime.build_preregistration()

    assert prereg["frozen_before_any_e1prime_run"] is True
    assert prereg["chrono_vehicle_variants"] == ["sedan_tmeasy", "bmw_e90_tmeasy", "uazbus_tmeasy"]
    assert len(prereg["row_pairs"]) == 24
    assert len(prereg["quick_row_pairs"]) == 3
    assert prereg["min_validation_units_per_variant"] == 20
    assert prereg["validation_units_per_variant"] == 24
    assert prereg["oracle_floor_candidate"] == "floor:v4_pertuned_full_episode"
    assert "payload_position_or_cg_height" in prereg["blocked_by_e0_without_new_connector"]

    selection_ids = {pair["selection_row"]["row_id"] for pair in prereg["row_pairs"]}
    validation_ids = {pair["validation_row"]["row_id"] for pair in prereg["row_pairs"]}
    assert selection_ids.isdisjoint(validation_ids)
    assert all(pair["selection_row"]["instance"] == pair["validation_row"]["instance"] for pair in prereg["row_pairs"])
    assert all(pair["selection_row"]["level"] == pair["validation_row"]["level"] for pair in prereg["row_pairs"])


def test_selection_resume_keeps_completed_pairs_and_drops_partial_pair(tmp_path, monkeypatch) -> None:
    prereg = _small_selection_prereg(pair_count=2, grid_count=2)
    rows_csv = tmp_path / "rows.csv"
    progress_jsonl = tmp_path / "progress.jsonl"
    variant = "sedan_tmeasy"
    completed_pair, partial_pair = prereg["row_pairs"]

    for grid in prereg["full_grid_values"]:
        selected = e1prime.d1b._as_selected(completed_pair["selection_row"])
        e1prime._append_row(
            rows_csv,
            e1prime._record(
                role="selection",
                pair_id=completed_pair["pair_id"],
                variant=variant,
                selected=selected,
                arm="fixed_star_selection_candidate",
                candidate="full_grid_selection",
                grid=tuple(grid),
                result=_fake_chrono_result(variant),
                score=1.0,
            ),
        )
    selected = e1prime.d1b._as_selected(partial_pair["selection_row"])
    e1prime._append_row(
        rows_csv,
        e1prime._record(
            role="selection",
            pair_id=partial_pair["pair_id"],
            variant=variant,
            selected=selected,
            arm="fixed_star_selection_candidate",
            candidate="full_grid_selection",
            grid=tuple(prereg["full_grid_values"][0]),
            result=_fake_chrono_result(variant),
            score=1.0,
        ),
    )

    calls = []

    def fake_run_chrono_episode(client, scenario, policy, *, requested_variant):
        calls.append(scenario["d1b_source"]["row_id"])
        return _fake_chrono_result(requested_variant)

    monkeypatch.setattr(e1prime, "ChronoWorkerClient", _DummyChronoClient)
    monkeypatch.setattr(e1prime.d1b, "run_chrono_episode", fake_run_chrono_episode)

    e1prime._run_selection_if_needed(
        prereg,
        resume=True,
        rows_csv=rows_csv,
        progress_jsonl=progress_jsonl,
        stderr_log=tmp_path / "stderr.log",
    )

    assert calls == [partial_pair["selection_row"]["row_id"]] * len(prereg["full_grid_values"])


def test_selection_retries_once_after_worker_error(tmp_path, monkeypatch) -> None:
    prereg = _small_selection_prereg(pair_count=1, grid_count=1)
    rows_csv = tmp_path / "rows.csv"
    progress_jsonl = tmp_path / "progress.jsonl"
    failures = {"remaining": 1}

    def fake_run_chrono_episode(client, scenario, policy, *, requested_variant):
        if failures["remaining"]:
            failures["remaining"] -= 1
            raise RuntimeError("worker stdout timeout after 120s")
        return _fake_chrono_result(requested_variant)

    monkeypatch.setattr(e1prime, "ChronoWorkerClient", _DummyChronoClient)
    monkeypatch.setattr(e1prime.d1b, "run_chrono_episode", fake_run_chrono_episode)

    e1prime._run_selection_if_needed(
        prereg,
        resume=True,
        rows_csv=rows_csv,
        progress_jsonl=progress_jsonl,
        stderr_log=tmp_path / "stderr.log",
    )

    rows = e1prime._read_csv_rows(rows_csv)
    assert len(rows) == 1
    assert rows[0]["role"] == "selection"


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

    fixed, pertuned, _summary = e1prime.choose_grids_from_selection(rows, prereg)

    assert fixed == (1.0, 1.0, 1.0)
    assert pertuned[("sedan_tmeasy", "S1-inst01-pair1")] == (1.8, 1.0, 1.0)
    assert pertuned[("sedan_tmeasy", "S2-inst02-pair1")] == (1.0, 1.0, 1.0)


def test_summarize_full_applies_two_variant_positive_rule() -> None:
    prereg = e1prime.build_preregistration()
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
            for arm in ("v4_pertuned", "native_oracle"):
                rows.append(
                    {
                        "role": "oracle_adequacy",
                        "variant": variant,
                        "pair_id": pair["pair_id"],
                        "row_id": pair["selection_row"]["row_id"],
                        "arm": arm,
                        "candidate": "best:floor:v4_pertuned_full_episode" if arm == "native_oracle" else "selection_same_instance_grid",
                        "chrono_outcome": "success",
                        "reset_obs_finite": "True",
                        "variant_match": "True",
                    }
                )
            rows.append(
                {
                    "role": "oracle_adequacy",
                    "variant": variant,
                    "pair_id": pair["pair_id"],
                    "row_id": pair["selection_row"]["row_id"],
                    "arm": "native_oracle_candidate",
                    "candidate": "floor:v4_pertuned_full_episode",
                    "chrono_outcome": "success",
                    "reset_obs_finite": "True",
                    "variant_match": "True",
                }
            )

    fixed, _pertuned, selection_summary = e1prime.choose_grids_from_selection(rows, prereg)
    summary = e1prime.summarize_full(rows, prereg, fixed_grid=fixed, selection_summary=selection_summary)

    assert summary["protocol_gates"]["all_passed"] is True
    assert summary["oracle_adequacy"]["gate_passed"] is True
    assert summary["decision"]["e1prime_full_verdict"] == "e1prime_spread_revival_positive"
    assert set(summary["decision"]["qualifying_variants"]) == {"sedan_tmeasy", "bmw_e90_tmeasy"}
    assert summary["pooled"]["primary_prize_pertuned_minus_fixed_star"]["n_pairs"] >= 60


def test_summarize_full_refuses_verdict_when_oracle_adequacy_missing() -> None:
    prereg = e1prime.build_preregistration()
    rows = []
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
            for arm in ("fixed_star", "v4_rls", "v4_pertuned", "native_oracle"):
                rows.append(
                    {
                        "role": "validation",
                        "variant": variant,
                        "pair_id": pair["pair_id"],
                        "row_id": pair["validation_row"]["row_id"],
                        "arm": arm,
                        "chrono_outcome": "success",
                        "reset_obs_finite": "True",
                        "variant_match": "True",
                    }
                )

    fixed, _pertuned, selection_summary = e1prime.choose_grids_from_selection(rows, prereg)
    summary = e1prime.summarize_full(rows, prereg, fixed_grid=fixed, selection_summary=selection_summary)

    assert summary["oracle_adequacy"]["gate_passed"] is False
    assert summary["protocol_gates"]["all_passed"] is False
    assert summary["decision"]["e1prime_full_verdict"] == "e1prime_oracle_inadequate_inconclusive"


def test_quick_smoke_decision_does_not_complete_e1prime() -> None:
    summary = {
        "protocol_gates": {"all_passed": True},
        "decision": {
            "e1prime_full_verdict": "e1prime_spread_revival_positive",
            "next_admitted_step": "E1' is complete; Track F remains blocked",
            "track_f_admitted": True,
        },
    }

    e1prime.apply_quick_smoke_decision(summary)

    assert summary["quick_mode_is_verdict"] is False
    assert summary["decision"]["e1prime_quick_verdict"] == "protocol_smoke_passed"
    assert summary["decision"]["e1prime_full_verdict"] == "not_run_quick_mode"
    assert summary["decision"]["track_f_admitted"] is False
    assert "before marking E1' complete" in summary["decision"]["next_admitted_step"]
