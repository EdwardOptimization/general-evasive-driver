from pathlib import Path

import pandas as pd
import pytest

from autodrift.forward_geometry_source_miner import (
    ForwardRelocationProposal,
    build_forward_geometry_source_summary,
    expand_forward_geometry_sources,
    forward_relocation_grid,
    run_forward_geometry_source_miner_from_rows,
    select_forward_geometry_source_rows,
    source_steps_for_reveal,
    validate_forward_longitudinal_offsets,
)


def _source_row(
    *,
    seed: int,
    source_body_x: float = 8.0,
    source_step: int = 40,
    variant: str = "warmup_removed",
    sequence_l2: float = 0.10,
) -> dict[str, object]:
    return {
        "seed": seed,
        "reveal_step": 72,
        "source_step": source_step,
        "source_body_x": source_body_x,
        "source_body_y": 0.0,
        "source_half_width": 0.5,
        "variant": variant,
        "capability_pair": f"pair-{seed % 2}",
        "preferred_reveal_bucket": f"bucket-{seed}",
        "sequence_action_l2_mean": sequence_l2,
        "matched_current_pass": True,
        "bucketed_current_pass": False,
    }


def test_source_steps_for_reveal_clamps_and_deduplicates():
    assert source_steps_for_reveal(16, offsets=(-32, -16, -8, 0)) == (0, 8, 16)


def test_forward_relocation_grid_rejects_negative_longitudinal_offsets():
    with pytest.raises(ValueError, match="negative longitudinal"):
        validate_forward_longitudinal_offsets((-1.0, 0.0))

    grid = forward_relocation_grid(longitudinal_offsets=(0.0, 2.0), lateral_offsets=(0.0,), half_width_inflations=(0.0,))
    assert [proposal.body_longitudinal_offset for proposal in grid] == [0.0, 2.0]


def test_expand_forward_geometry_sources_filters_geometry_first():
    rows = pd.DataFrame(
        [
            _source_row(seed=1, source_body_x=8.0),
            _source_row(seed=2, source_body_x=3.0),
        ]
    )
    proposals = [ForwardRelocationProposal(0.0, 0.0, 0.0)]

    accepted, rejected = expand_forward_geometry_sources(rows, proposals=proposals)

    assert len(accepted) == 1
    assert int(accepted.iloc[0]["seed"]) == 1
    assert bool(accepted.iloc[0]["forward_geometry_pass"]) is True
    assert len(rejected) == 1
    assert "source_body_x_too_close" in str(rejected.iloc[0]["rejection_reason"])


def test_select_forward_geometry_source_rows_enforces_caps_and_history_variants():
    rows = pd.DataFrame(
        [
            _source_row(seed=1, source_body_x=10.0, variant="warmup_removed"),
            _source_row(seed=1, source_body_x=9.0, variant="warmup_shortened_8"),
            _source_row(seed=2, source_body_x=8.0, variant="warmup_shortened_8"),
            _source_row(seed=3, source_body_x=8.0, variant="zero_current_response"),
        ]
    )
    accepted, _ = expand_forward_geometry_sources(rows, proposals=[ForwardRelocationProposal(0.0, 0.0, 0.0)])

    selected = select_forward_geometry_source_rows(
        accepted,
        max_candidates=10,
        per_seed_cap=1,
        per_capability_pair_cap=10,
        per_reveal_bucket_cap=10,
        per_variant_cap=1,
    )

    assert len(selected) == 2
    assert set(selected["variant"]) == {"warmup_removed", "warmup_shortened_8"}
    assert selected["seed"].value_counts().max() == 1
    assert selected["variant"].value_counts().max() == 1


def test_forward_geometry_summary_and_runner_write_artifacts(tmp_path: Path):
    source_csv = tmp_path / "source_geometry_rows.csv"
    pd.DataFrame([_source_row(seed=1), _source_row(seed=2, source_body_x=3.0)]).to_csv(source_csv, index=False)

    summary = run_forward_geometry_source_miner_from_rows(
        source_geometry_rows_path=source_csv,
        run_dir=tmp_path / "run",
        max_candidates=8,
        per_seed_cap=2,
        per_capability_pair_cap=4,
        per_reveal_bucket_cap=4,
        per_variant_cap=4,
    )

    assert summary["geometry_pass_rows"] > 0
    assert summary["selected_candidate_rows"] > 0
    assert summary["source_mining_started"] is False
    assert summary["replay_started"] is False
    assert (tmp_path / "run" / "forward_geometry_source_rows.csv").exists()
    assert (tmp_path / "run" / "selected_candidate_rows.csv").exists()
    assert (tmp_path / "run" / "summary.json").exists()


def test_build_forward_geometry_source_summary_keeps_guardrails_false():
    rows = pd.DataFrame([_source_row(seed=1)])
    accepted, rejected = expand_forward_geometry_sources(rows, proposals=[ForwardRelocationProposal(0.0, 0.0, 0.0)])
    selected = select_forward_geometry_source_rows(
        accepted,
        max_candidates=8,
        per_seed_cap=2,
        per_capability_pair_cap=4,
        per_reveal_bucket_cap=4,
        per_variant_cap=4,
    )

    summary = build_forward_geometry_source_summary(
        source_rows=rows,
        candidates=accepted,
        selected=selected,
        rejected=rejected,
    )

    assert summary["source_rows"] == 1
    assert summary["source_mining_started"] is False
    assert summary["source_preflight_started"] is False
    assert summary["training_started"] is False
