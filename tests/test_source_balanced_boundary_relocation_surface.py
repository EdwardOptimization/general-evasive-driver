from pathlib import Path

import pandas as pd

import autodrift.source_balanced_boundary_relocation_surface as source_balanced
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec
from autodrift.source_balanced_boundary_relocation_surface import (
    SourceBalanceQuotas,
    build_source_budget,
    mark_balanced_export_rows,
    physical_pair_key,
    run_source_balanced_boundary_artifact_smoke,
    select_source_balanced_candidates,
    source_obstacle_bucket,
    write_source_balance_artifacts,
)


def _candidate(
    *,
    left_seed: int,
    left_step: int,
    right_seed: int,
    right_step: int,
    margin_gap: float,
    first_action_distance: float,
    checkpoint_label: str = "proof",
    target: str = "brake",
    obstacle_distance: float = 20.0,
    obstacle_lateral_offset: float = 0.0,
) -> dict[str, object]:
    return {
        "variant": "wrong_matched_history",
        "checkpoint_label": checkpoint_label,
        "target": target,
        "left_seed": left_seed,
        "left_step": left_step,
        "right_seed": right_seed,
        "right_step": right_step,
        "normal_margin": 0.1,
        "margin_gap": margin_gap,
        "first_action_distance": first_action_distance,
        "visible_distance": 0.01,
        "obstacle_distance": obstacle_distance,
        "obstacle_lateral_offset": obstacle_lateral_offset,
    }


def _boundary_row(
    *,
    left_seed: int,
    left_step: int,
    right_seed: int,
    right_step: int,
    normal_margin: float,
    margin_gap: float = 0.03,
    checkpoint_label: str = "proof",
    target: str = "brake",
    accepted: bool = True,
    success_drop: bool = True,
) -> dict[str, object]:
    return {
        "variant": "wrong_matched_history",
        "accepted": accepted,
        "success_drop": success_drop,
        "normal_success": True,
        "variant_success": not success_drop,
        "checkpoint_label": checkpoint_label,
        "target": target,
        "left_seed": left_seed,
        "left_step": left_step,
        "right_seed": right_seed,
        "right_step": right_step,
        "normal_margin": normal_margin,
        "variant_margin": normal_margin - margin_gap,
        "margin_gap": margin_gap,
    }


def test_physical_pair_key_matches_robustness_key():
    row = _candidate(left_seed=10, left_step=20, right_seed=30, right_step=40, margin_gap=1.0, first_action_distance=0.5)

    assert physical_pair_key(row) == "10:20:30:40"


def test_source_obstacle_bucket_uses_source_geometry_when_available():
    row = {
        "source_obstacle_body_x": 24.9,
        "source_obstacle_body_y": -0.1,
        "obstacle_distance": 80.0,
        "obstacle_lateral_offset": 9.0,
    }

    assert source_obstacle_bucket(row, distance_bucket_width=5.0, lateral_bucket_width=1.0) == "x=20.000-25.000|y=-1.000-0.000"


def test_source_budget_reports_pair_dominance_and_ready_state():
    rows = [
        _candidate(left_seed=1, left_step=10 + index, right_seed=2, right_step=20 + index, margin_gap=0.5, first_action_distance=0.2)
        for index in range(4)
    ]
    rows.extend(
        _candidate(left_seed=10 + index, left_step=30, right_seed=20 + index, right_step=40, margin_gap=0.1, first_action_distance=0.1)
        for index in range(8)
    )
    summary, budget_rows = build_source_budget(
        pd.DataFrame(rows),
        min_eligible_physical_pairs=10,
        max_candidate_pair_fraction=0.50,
    )

    assert summary["candidate_wrong_history_rows"] == 12
    assert summary["eligible_physical_pairs"] == 12
    assert summary["source_budget_ready"]
    assert len(budget_rows) == 12


def test_source_budget_fails_closed_when_too_few_physical_pairs():
    rows = [
        _candidate(left_seed=1, left_step=10, right_seed=2, right_step=20, margin_gap=0.5, first_action_distance=0.2)
        for _ in range(6)
    ]

    summary, _budget_rows = build_source_budget(pd.DataFrame(rows), min_eligible_physical_pairs=10)

    assert not summary["source_budget_ready"]
    assert summary["decision"] == "source_budget_insufficient_or_dominated"
    assert summary["eligible_physical_pairs"] == 1


def test_balanced_candidate_selection_round_robins_instead_of_global_top_k():
    rows = []
    for index in range(6):
        rows.append(
            _candidate(
                left_seed=1,
                left_step=10,
                right_seed=2,
                right_step=20,
                margin_gap=1.0 - index * 0.01,
                first_action_distance=0.5,
            )
        )
    for pair_index in range(1, 5):
        rows.append(
            _candidate(
                left_seed=100 + pair_index,
                left_step=10 + pair_index,
                right_seed=200 + pair_index,
                right_step=20 + pair_index,
                margin_gap=0.2,
                first_action_distance=0.2,
                target="yaw" if pair_index % 2 else "brake",
            )
        )

    selected, _rejected, summary = select_source_balanced_candidates(
        pd.DataFrame(rows),
        quotas=SourceBalanceQuotas(
            max_candidates=5,
            max_candidates_per_physical_pair=1,
            max_candidates_per_checkpoint_target=10,
            target_min_physical_pairs=5,
            target_min_left_steps=5,
            target_min_targets=2,
        ),
    )

    assert len(selected) == 5
    assert selected["physical_pair_key"].nunique() == 5
    assert summary["decision"] == "source_balanced_candidates_ready"


def test_balanced_export_marks_extra_rows_non_exportable_and_gates_pass():
    rows = []
    for pair_index in range(10):
        for duplicate in range(9):
            rows.append(
                _boundary_row(
                    left_seed=100 + pair_index,
                    left_step=10 + pair_index,
                    right_seed=200 + pair_index,
                    right_step=20 + pair_index,
                    normal_margin=0.002 + 0.001 * (pair_index % 3),
                    checkpoint_label=f"p{pair_index % 3}",
                    target="brake" if pair_index % 2 else "yaw",
                    margin_gap=0.03 + 0.001 * duplicate,
                )
            )

    marked, summary, gates = mark_balanced_export_rows(
            pd.DataFrame(rows),
            quotas=SourceBalanceQuotas(
                max_candidates=90,
                max_accepted_rows_per_physical_pair=8,
                max_rows_per_pair_fraction=0.25,
            ),
        margin_bucket_width=0.001,
        control_checkpoint_label="control",
    )

    assert int(marked["balanced_exportable"].sum()) == 80
    assert summary["decision"] == "source_balanced_boundary_export_pass"
    assert summary["passed"]
    assert all(row["passed"] for row in gates)
    assert "physical_pair_accepted_cap" in set(marked["balance_rejection_reason"])


def test_balanced_export_fails_when_only_six_physical_pairs_exist():
    rows = [
        _boundary_row(
            left_seed=100 + pair_index,
            left_step=10 + pair_index,
            right_seed=200 + pair_index,
            right_step=20 + pair_index,
            normal_margin=0.002,
            checkpoint_label=f"p{pair_index % 3}",
            target="brake" if pair_index % 2 else "yaw",
        )
        for pair_index in range(6)
        for _duplicate in range(2)
    ]

    _marked, summary, gates = mark_balanced_export_rows(
        pd.DataFrame(rows),
        quotas=SourceBalanceQuotas(max_candidates=12, max_accepted_rows_per_physical_pair=2),
        margin_bucket_width=0.001,
        control_checkpoint_label="control",
    )

    assert summary["decision"] == "reject_duplicate_dominated_boundary_surface"
    failed = {row["gate"] for row in gates if not row["passed"]}
    assert "accepted_wrong_physical_pairs" in failed


def test_write_source_balance_artifacts(tmp_path: Path):
    candidates = pd.DataFrame(
        [_candidate(left_seed=1, left_step=10, right_seed=2, right_step=20, margin_gap=0.5, first_action_distance=0.2)]
    )
    source_budget_summary, source_budget_rows = build_source_budget(candidates, min_eligible_physical_pairs=1)
    selected, rejected, _selection_summary = select_source_balanced_candidates(
        candidates,
        quotas=SourceBalanceQuotas(max_candidates=1, target_min_physical_pairs=1),
    )
    marked, balanced_summary, gates = mark_balanced_export_rows(
        pd.DataFrame(
            [
                _boundary_row(
                    left_seed=1,
                    left_step=10,
                    right_seed=2,
                    right_step=20,
                    normal_margin=0.002,
                )
            ]
        ),
        quotas=SourceBalanceQuotas(max_candidates=1, max_accepted_rows_per_physical_pair=1),
        margin_bucket_width=0.001,
        control_checkpoint_label="control",
    )

    summary = write_source_balance_artifacts(
        run_dir=tmp_path,
        source_budget_summary=source_budget_summary,
        source_budget_rows=source_budget_rows,
        selected_candidates=selected,
        rejected_candidates=rejected,
        marked_boundary_rows=marked,
        balanced_summary=balanced_summary,
        robustness_gates=gates,
    )

    assert summary["training_started"] is False
    assert (tmp_path / "source_budget_summary.json").exists()
    assert (tmp_path / "balanced_candidate_rows.csv").exists()
    assert (tmp_path / "balanced_accepted_wrong_history_rows.csv").exists()


def test_existing_artifact_smoke_reads_csv_without_mining(tmp_path: Path):
    candidate_csv = tmp_path / "candidates.csv"
    boundary_csv = tmp_path / "boundary.csv"
    pd.DataFrame(
        [
            _candidate(
                left_seed=10 + index,
                left_step=20 + index,
                right_seed=30 + index,
                right_step=40 + index,
                margin_gap=0.4,
                first_action_distance=0.2,
            )
            for index in range(10)
        ]
    ).to_csv(candidate_csv, index=False)
    pd.DataFrame(
        [
            _boundary_row(
                left_seed=10 + index,
                left_step=20 + index,
                right_seed=30 + index,
                right_step=40 + index,
                normal_margin=0.002 + 0.001 * (index % 3),
                checkpoint_label=f"p{index % 3}",
                target="brake" if index % 2 else "yaw",
            )
            for index in range(10)
            for _duplicate in range(8)
        ]
    ).to_csv(boundary_csv, index=False)

    summary = run_source_balanced_boundary_artifact_smoke(
        candidate_csv=candidate_csv,
        boundary_rows_csv=boundary_csv,
        run_dir=tmp_path / "run",
        quotas=SourceBalanceQuotas(
            max_candidates=10,
            max_candidates_per_physical_pair=1,
            max_accepted_rows_per_physical_pair=8,
        ),
        min_eligible_physical_pairs=10,
        max_candidate_pair_fraction=0.25,
        margin_bucket_width=0.001,
        control_checkpoint_label="control",
    )

    assert summary["full_new_mining_run"] is False
    assert summary["source_budget"]["source_budget_ready"]
    assert summary["balanced_summary"]["passed"]
    assert (tmp_path / "run" / "summary.json").exists()


def test_full_relocation_fails_closed_before_replay_when_source_budget_is_insufficient(
    tmp_path: Path,
    monkeypatch,
):
    outcome_csv = tmp_path / "outcome.csv"
    pd.DataFrame(
        [
            _candidate(
                left_seed=1,
                left_step=10,
                right_seed=2,
                right_step=20,
                margin_gap=0.5,
                first_action_distance=0.2,
                checkpoint_label="proof",
            )
            for _ in range(4)
        ]
    ).to_csv(outcome_csv, index=False)

    def _unexpected_replay(*_args, **_kwargs):
        raise AssertionError("source-budget failure should not enter relocation replay")

    monkeypatch.setattr(source_balanced, "load_env_config", _unexpected_replay)
    monkeypatch.setattr(source_balanced, "load_actor_critic_checkpoint", _unexpected_replay)
    monkeypatch.setattr(source_balanced, "build_boundary_relocation_rows", _unexpected_replay)

    summary = source_balanced.run_source_balanced_boundary_relocation_surface(
        checkpoint_specs=(CheckpointSpec(label="proof", path=tmp_path / "proof.pt"),),
        env_config_path=tmp_path / "env.json",
        outcome_csv=outcome_csv,
        run_dir=tmp_path / "run",
        quotas=SourceBalanceQuotas(max_candidates=4, target_min_physical_pairs=10),
        delay_steps=10,
        max_continuation_steps=60,
        target_normal_margins=(0.005,),
        half_width_inflations=(0.0,),
        body_longitudinals=None,
        body_laterals=None,
        body_longitudinal_offsets=None,
        body_lateral_offsets=None,
        min_half_width=0.3,
        max_half_width=2.5,
        min_normal_margin=0.0,
        max_normal_margin=0.04,
        min_margin_gap=0.04,
        report_variants=("wrong_matched_history",),
        device="cpu",
        min_eligible_physical_pairs=10,
        margin_bucket_width=0.001,
        control_checkpoint_label="control",
    )

    assert summary["decision"] == "source_budget_not_ready"
    assert summary["relocation_replay_started"] is False
    assert summary["full_new_mining_run"] is False
    assert (tmp_path / "run" / "source_budget_summary.json").exists()
    assert (tmp_path / "run" / "boundary_relocation_rows.csv").exists()


def test_full_relocation_passes_source_balanced_candidates_to_replay(tmp_path: Path, monkeypatch):
    outcome_csv = tmp_path / "outcome.csv"
    rows = []
    for duplicate in range(6):
        rows.append(
            _candidate(
                left_seed=1,
                left_step=10,
                right_seed=2,
                right_step=20,
                margin_gap=1.0 - duplicate * 0.01,
                first_action_distance=0.5,
                checkpoint_label="proof",
                target="brake",
            )
        )
    for pair_index in range(1, 5):
        rows.append(
            _candidate(
                left_seed=100 + pair_index,
                left_step=10 + pair_index,
                right_seed=200 + pair_index,
                right_step=20 + pair_index,
                margin_gap=0.2,
                first_action_distance=0.2,
                checkpoint_label="proof",
                target="yaw" if pair_index % 2 else "brake",
            )
        )
    pd.DataFrame(rows).to_csv(outcome_csv, index=False)

    class _DummyModel:
        def eval(self):
            return None

    captured: dict[str, object] = {}

    monkeypatch.setattr(source_balanced, "resolve_device", lambda device: device)
    monkeypatch.setattr(source_balanced, "load_env_config", lambda _path: object())
    monkeypatch.setattr(source_balanced, "load_actor_critic_checkpoint", lambda _path, device: (_DummyModel(), {}))
    monkeypatch.setattr(source_balanced, "response_feature_dim_for_model", lambda _model: 0)
    monkeypatch.setattr(source_balanced, "collect_requested_source_balanced_snapshots", lambda **_kwargs: {})

    def _fake_build_boundary_relocation_rows(*, candidate_rows, **_kwargs):
        captured["physical_pairs"] = list(candidate_rows["physical_pair_key"])
        captured["left_seeds"] = list(candidate_rows["left_seed"])
        rows = []
        for candidate_id, row in candidate_rows.reset_index(drop=True).iterrows():
            boundary = _boundary_row(
                accepted=True,
                success_drop=True,
                left_seed=int(row["left_seed"]),
                left_step=int(row["left_step"]),
                right_seed=int(row["right_seed"]),
                right_step=int(row["right_step"]),
                normal_margin=0.002,
                checkpoint_label=str(row["checkpoint_label"]),
                target=str(row["target"]),
            )
            boundary.update(
                {
                    "candidate_id": int(candidate_id),
                    "source_pair_id": int(row.get("pair_id", candidate_id)),
                    "normal_near_boundary": True,
                    "base_wrong_margin_gap": float(row["margin_gap"]),
                    "base_wrong_first_action_distance": float(row["first_action_distance"]),
                }
            )
            rows.append(boundary)
        return rows

    monkeypatch.setattr(source_balanced, "build_boundary_relocation_rows", _fake_build_boundary_relocation_rows)

    summary = source_balanced.run_source_balanced_boundary_relocation_surface(
        checkpoint_specs=(CheckpointSpec(label="proof", path=tmp_path / "proof.pt"),),
        env_config_path=tmp_path / "env.json",
        outcome_csv=outcome_csv,
        run_dir=tmp_path / "run",
        quotas=SourceBalanceQuotas(
            max_candidates=5,
            max_candidates_per_physical_pair=1,
            target_min_physical_pairs=5,
            target_min_left_steps=5,
            target_min_targets=2,
        ),
        delay_steps=10,
        max_continuation_steps=60,
        target_normal_margins=(0.005,),
        half_width_inflations=(0.0,),
        body_longitudinals=None,
        body_laterals=None,
        body_longitudinal_offsets=None,
        body_lateral_offsets=None,
        min_half_width=0.3,
        max_half_width=2.5,
        min_normal_margin=0.0,
        max_normal_margin=0.04,
        min_margin_gap=0.04,
        report_variants=("wrong_matched_history",),
        device="cpu",
        min_eligible_physical_pairs=5,
        max_candidate_pair_fraction=1.0,
        margin_bucket_width=0.001,
        control_checkpoint_label="control",
    )

    assert summary["relocation_replay_started"] is True
    assert summary["candidate_selection_summary"]["selected_rows"] == 5
    assert len(set(captured["physical_pairs"])) == 5
    assert captured["left_seeds"].count(1) == 1
    assert (tmp_path / "run" / "balanced_candidate_rows.csv").exists()
    assert (tmp_path / "run" / "surface_summary.csv").exists()
