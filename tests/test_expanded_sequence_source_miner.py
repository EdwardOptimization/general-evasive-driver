from pathlib import Path

import pandas as pd
import pytest

from autodrift.expanded_sequence_source_miner import (
    classify_expanded_source,
    expand_sequence_sources,
    expanded_source_diversity,
    run_expanded_sequence_source_miner,
)


def test_classify_expanded_source_uses_tiers_and_rejections():
    accepted, reason, tier = classify_expanded_source(
        _rollout_row(source_index=1, margin=0.7),
        core_margin_window=0.5,
        near_margin_window=1.0,
        support_margin_window=2.0,
    )
    assert accepted
    assert reason == "near_margin_window"
    assert tier == "near_boundary"

    accepted, reason, tier = classify_expanded_source(
        _rollout_row(source_index=2, margin=1.5),
        core_margin_window=0.5,
        near_margin_window=1.0,
        support_margin_window=2.0,
    )
    assert accepted
    assert reason == "support_margin_window"
    assert tier == "support_boundary"

    accepted, reason, tier = classify_expanded_source(
        _rollout_row(source_index=3, margin=0.1, variant="shuffled_history"),
        core_margin_window=0.5,
        near_margin_window=1.0,
        support_margin_window=2.0,
    )
    assert not accepted
    assert reason == "unsupported_history_variant"
    assert tier == ""


def test_expand_sequence_sources_preserves_provenance_and_flags():
    rows = pd.DataFrame(
        [
            _rollout_row(source_index=0, margin=0.3),
            _rollout_row(source_index=1, margin=0.7),
            _rollout_row(source_index=2, margin=3.0),
        ]
    )

    expanded, rejected, diversity = expand_sequence_sources(
        rows,
        original_boundary_source_indices={0},
        accepted_sequence_source_indices={1},
        core_margin_window=0.5,
        near_margin_window=1.0,
        support_margin_window=2.0,
    )

    assert [row["source_index"] for row in expanded] == [0, 1]
    assert rejected[0]["source_index"] == 2
    assert expanded[0]["original_m609_boundary"] is True
    assert expanded[1]["m613_accepted_sequence"] is True
    assert diversity.rows == 2


def test_expanded_source_diversity_requires_source_breadth():
    rows = pd.DataFrame(
        [
            _rollout_row(
                source_index=index,
                margin=0.4 if index < 10 else 1.5,
                surface="fresh" if index % 2 == 0 else "ood",
                variant="delayed_history" if index % 2 == 0 else "wrong_matched_history",
                target="future_yaw_response" if index % 3 else "future_braking_deceleration",
                left_seed=index,
                right_seed=100 + index,
            )
            for index in range(24)
        ]
    )

    diversity = expanded_source_diversity(rows)

    assert diversity.rows == 24
    assert diversity.unique_physical_pairs == 24
    assert diversity.unique_left_seeds == 24
    assert diversity.surfaces == 2
    assert diversity.variants == 2
    assert diversity.targets == 2
    assert diversity.pass_diversity


def test_run_expanded_sequence_source_miner_writes_artifacts(tmp_path: Path):
    source_rollouts = pd.DataFrame(
        [
            _rollout_row(
                source_index=index,
                margin=0.4 if index < 12 else 1.5,
                surface="fresh" if index % 2 == 0 else "ood",
                variant="delayed_history" if index % 2 == 0 else "wrong_matched_history",
                target="future_yaw_response" if index % 3 else "future_braking_deceleration",
                left_seed=index,
                right_seed=100 + index,
            )
            for index in range(24)
        ]
        + [_rollout_row(source_index=99, margin=3.0)]
    )
    source_rollouts_csv = tmp_path / "source_rollouts.csv"
    boundary_csv = tmp_path / "boundary.csv"
    accepted_csv = tmp_path / "accepted.csv"
    source_rollouts.to_csv(source_rollouts_csv, index=False)
    pd.DataFrame([{"source_index": 0}, {"source_index": 1}]).to_csv(boundary_csv, index=False)
    pd.DataFrame([{"source_index": 5}]).to_csv(accepted_csv, index=False)

    summary = run_expanded_sequence_source_miner(
        source_rollouts_csv=source_rollouts_csv,
        original_boundary_source_rows_csv=boundary_csv,
        accepted_sequences_csv=accepted_csv,
        core_margin_window=0.5,
        near_margin_window=1.0,
        support_margin_window=2.0,
        run_dir=tmp_path / "run",
    )

    assert summary["expanded_source_rows"] == 24
    assert summary["rejected_source_rows"] == 1
    assert summary["original_m609_boundary_rows_included"] == 2
    assert summary["m613_accepted_sequence_rows_included"] == 1
    assert summary["diversity_pass"] is True
    assert summary["actor_parameters_changed"] is False
    assert summary["ppo_used"] is False
    assert (tmp_path / "run" / "expanded_sequence_source_rows.csv").exists()
    assert (tmp_path / "run" / "rejected_sequence_source_rows.csv").exists()
    assert (tmp_path / "run" / "summary.json").exists()


def test_invalid_windows_raise():
    with pytest.raises(ValueError, match="core_margin_window"):
        classify_expanded_source(
            _rollout_row(source_index=1, margin=0.7),
            core_margin_window=1.0,
            near_margin_window=0.5,
            support_margin_window=2.0,
        )


def _rollout_row(
    *,
    source_index: int,
    margin: float,
    surface: str = "fresh",
    variant: str = "delayed_history",
    target: str = "future_yaw_response",
    left_seed: int | None = None,
    left_step: int = 3,
    right_seed: int | None = None,
    right_step: int = 3,
) -> dict[str, object]:
    left_seed = source_index if left_seed is None else left_seed
    right_seed = 100 + source_index if right_seed is None else right_seed
    return {
        "source_index": source_index,
        "coupling_row_index": 1000 + source_index,
        "surface": surface,
        "target": target,
        "variant": variant,
        "left_seed": left_seed,
        "right_seed": right_seed,
        "left_step": left_step,
        "right_step": right_step,
        "capability_z_distance": 0.2,
        "action_distance": 0.01,
        "coupling_gap": 20.0,
        "base_steer": 0.1,
        "base_throttle": 0.0,
        "base_brake": 0.2,
        "baseline_success": True,
        "baseline_collision": False,
        "baseline_off_road": False,
        "baseline_spin_out": False,
        "baseline_terminal_reason": "max_steps",
        "baseline_margin": margin,
        "baseline_risk_score": -margin,
        "obstacle_completed": True,
        "continuation_steps": 80,
    }
