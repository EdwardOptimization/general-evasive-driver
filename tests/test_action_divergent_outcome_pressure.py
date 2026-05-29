from pathlib import Path

import pandas as pd

from autodrift.action_divergent_outcome_pressure import (
    RelocationProposal,
    action_divergent_candidate_pool,
    build_outcome_pressure_rows,
    relocation_grid,
    run_action_divergent_outcome_pressure_constructor,
    select_source_balanced_candidates,
)
from autodrift.artifacts import read_json


def _row(
    *,
    selected_index: int,
    seed: int,
    variant: str,
    sequence_l2: float,
    first_l2: float = 0.0,
    normal_margin: float = 0.12,
    variant_margin: float = 0.05,
    margin_gap: float | None = None,
    normal_success: bool = True,
    variant_success: bool = True,
    capability_pair: str = "brake->combined",
    bucket: str = "bucket-a",
    matched_current: bool = True,
    bucketed_current: bool = False,
) -> dict[str, object]:
    return {
        "selected_index": selected_index,
        "source_index": selected_index + 100,
        "seed": seed,
        "reveal_step": 48,
        "preferred_fault": "preferred",
        "preferred_fault_family": capability_pair.split("->")[0],
        "wrong_fault": "wrong",
        "wrong_fault_family": capability_pair.split("->")[-1],
        "capability_pair": capability_pair,
        "preferred_reveal_bucket": bucket,
        "wrong_reveal_bucket": bucket,
        "matched_current_pass": matched_current,
        "bucketed_current_pass": bucketed_current,
        "variant": variant,
        "normal_success": normal_success,
        "variant_success": variant_success,
        "success_drop": bool(normal_success and not variant_success),
        "normal_margin": normal_margin,
        "normal_margin_band": "preferred_0p02_0p25",
        "normal_broad_near_boundary": True,
        "normal_preferred_near_boundary": True,
        "variant_margin": variant_margin,
        "margin_gap": normal_margin - variant_margin if margin_gap is None else margin_gap,
        "first_action_l2": first_l2,
        "sequence_action_l2_mean": sequence_l2,
        "sequence_action_l2_max": sequence_l2,
        "sequence_action_critical": sequence_l2 >= 0.025,
        "outcome_critical": False,
        "warmup_history_positive": False,
    }


def test_candidate_pool_counts_only_history_variants_as_candidates():
    frame = pd.DataFrame(
        [
            _row(selected_index=1, seed=10, variant="zero_current_response", sequence_l2=0.4),
            _row(selected_index=1, seed=10, variant="reset_hidden", sequence_l2=0.3),
            _row(selected_index=2, seed=11, variant="warmup_removed", sequence_l2=0.05),
            _row(selected_index=2, seed=11, variant="same_recent_wrong_warmup_history", sequence_l2=0.01),
        ]
    )

    pool, rejected = action_divergent_candidate_pool(frame, min_sequence_action_l2=0.025)

    assert len(pool) == 1
    assert pool.iloc[0]["variant"] == "warmup_removed"
    assert pool.iloc[0]["variant_family"] == "history"
    control_only = rejected[rejected["selected_index"] == 1]
    assert len(control_only) == 1
    assert "control_only_action_divergence" in str(control_only.iloc[0]["rejection_reason"])


def test_relocation_pressure_rows_are_proxy_only_and_history_positive():
    frame = pd.DataFrame(
        [
            _row(
                selected_index=3,
                seed=12,
                variant="warmup_removed",
                sequence_l2=0.05,
                normal_margin=0.12,
                variant_margin=0.05,
            )
        ]
    )
    pool, _ = action_divergent_candidate_pool(frame, min_sequence_action_l2=0.025)
    proposals = [RelocationProposal(0.0, 0.0, 0.06)]

    pressure, rejected = build_outcome_pressure_rows(
        pool,
        proposals=proposals,
        min_margin_gap=0.02,
        max_relocations_per_candidate=4,
    )

    assert rejected.empty
    assert len(pressure) == 1
    row = pressure.iloc[0]
    assert bool(row["proxy_only"])
    assert bool(row["requires_replay"])
    assert bool(row["proxy_history_positive"])
    assert row["proxy_normal_margin"] > 0.0
    assert row["proxy_variant_margin"] < 0.0


def test_source_balanced_selection_caps_by_capability_pair():
    rows = []
    for index in range(4):
        rows.append(
            _row(
                selected_index=index,
                seed=20 + index,
                variant="warmup_removed",
                sequence_l2=0.10 - index * 0.01,
                capability_pair="a->b",
            )
        )
    rows.append(
        _row(
            selected_index=10,
            seed=30,
            variant="delayed_warmup_history_8",
            sequence_l2=0.06,
            capability_pair="c->d",
        )
    )
    pool, _ = action_divergent_candidate_pool(pd.DataFrame(rows), min_sequence_action_l2=0.025)

    selected = select_source_balanced_candidates(pool, max_candidates=10, per_capability_pair_cap=1)

    assert len(selected) == 2
    assert selected["capability_pair"].value_counts().max() == 1
    assert set(selected["capability_pair"]) == {"a->b", "c->d"}


def test_constructor_writes_schema_and_contract_flags(tmp_path: Path):
    outcome_csv = tmp_path / "outcome_rows.csv"
    pd.DataFrame(
        [
            _row(
                selected_index=1,
                seed=10,
                variant="zero_current_response",
                sequence_l2=0.4,
                normal_margin=0.12,
                variant_margin=0.01,
            ),
            _row(
                selected_index=2,
                seed=11,
                variant="warmup_removed",
                sequence_l2=0.05,
                normal_margin=0.12,
                variant_margin=0.05,
                capability_pair="x->y",
                bucket="bucket-b",
            ),
        ]
    ).to_csv(outcome_csv, index=False)

    run_dir = tmp_path / "run"
    summary = run_action_divergent_outcome_pressure_constructor(
        outcome_rows_path=outcome_csv,
        run_dir=run_dir,
        max_candidates=8,
        per_capability_pair_cap=4,
        longitudinal_offsets=(0.0,),
        lateral_offsets=(0.0,),
        half_width_inflations=(0.06,),
    )
    persisted = read_json(run_dir / "summary.json")

    assert summary["candidate_rows"] == 1
    assert summary["outcome_pressure_rows"] == 1
    assert summary["history_positive_rows"] == 1
    assert summary["control_action_divergent_rows"] == 1
    assert persisted["training_started"] is False
    assert persisted["ppo_used"] is False
    assert persisted["actor_input_contract_changed"] is False
    assert persisted["proxy_only"] is True
    assert (run_dir / "candidate_rows.csv").exists()
    assert (run_dir / "outcome_pressure_rows.csv").exists()
    assert (run_dir / "history_positive_rows.csv").exists()


def test_relocation_grid_is_deterministic():
    grid = relocation_grid(
        longitudinal_offsets=(0.0, 1.0),
        lateral_offsets=(-0.2, 0.2),
        half_width_inflations=(0.0, 0.1),
    )

    assert [proposal.body_longitudinal_offset for proposal in grid[:4]] == [0.0, 0.0, 0.0, 0.0]
    assert len(grid) == 8
