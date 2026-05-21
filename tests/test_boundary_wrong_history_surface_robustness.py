from pathlib import Path

import pandas as pd

from autodrift.boundary_wrong_history_surface_robustness import (
    accepted_wrong_history_rows,
    build_gate_rows,
    decision_from_gates,
    run_boundary_wrong_history_surface_robustness,
    summarize_surface,
)


def _row(
    *,
    variant: str = "wrong_matched_history",
    accepted: bool = True,
    checkpoint_label: str = "m102",
    target: str = "brake",
    left_step: int = 10,
    right_step: int = 20,
    normal_margin: float = 0.006,
    success_drop: bool = True,
) -> dict[str, object]:
    return {
        "variant": variant,
        "accepted": accepted,
        "checkpoint_label": checkpoint_label,
        "target": target,
        "left_seed": 1,
        "left_step": left_step,
        "right_seed": 2,
        "right_step": right_step,
        "normal_margin": normal_margin,
        "margin_gap": 0.01,
        "success_drop": success_drop,
    }


def test_accepted_wrong_history_rows_filters_variant_and_acceptance():
    frame = pd.DataFrame(
        [
            _row(variant="wrong_matched_history", accepted=True),
            _row(variant="reset_hidden", accepted=True),
            _row(variant="wrong_matched_history", accepted=False),
        ]
    )

    accepted = accepted_wrong_history_rows(frame, margin_bucket_width=0.01)

    assert len(accepted) == 1
    assert accepted.iloc[0]["physical_pair_key"] == "1:10:2:20"
    assert accepted.iloc[0]["normal_margin_bucket"] == "0.000-0.010"


def test_summary_exposes_duplicate_dominated_surface():
    frame = pd.DataFrame(
        [
            _row(checkpoint_label="m102", target="brake", left_step=10, right_step=20),
            _row(checkpoint_label="m105", target="yaw", left_step=10, right_step=20),
            _row(checkpoint_label="m105", target="lateral", left_step=11, right_step=21),
            _row(variant="zero_current_response", accepted=True, left_step=12, right_step=22),
        ]
    )

    summary = summarize_surface(frame, margin_bucket_width=0.01, control_checkpoint_label="m62")

    assert summary["accepted_wrong_rows"] == 3
    assert summary["accepted_wrong_physical_pairs"] == 2
    assert summary["accepted_wrong_checkpoints"] == 2
    assert summary["accepted_wrong_targets"] == 3
    assert summary["accepted_wrong_normal_margin_buckets"] == 1
    assert summary["max_rows_per_physical_pair"] == 2
    assert summary["control_accepted_wrong_rows"] == 0
    assert summary["accepted_zero_current_rows"] == 1


def test_gate_decision_rejects_duplicate_dominated_surface():
    summary = {
        "accepted_wrong_rows": 12,
        "accepted_wrong_physical_pairs": 3,
        "accepted_wrong_left_steps": 3,
        "accepted_wrong_checkpoints": 2,
        "accepted_wrong_targets": 3,
        "accepted_wrong_normal_margin_buckets": 1,
        "accepted_wrong_success_drop_fraction": 1.0,
        "max_rows_per_physical_pair_fraction": 0.5,
        "control_accepted_wrong_rows": 0,
    }

    gates = build_gate_rows(
        summary,
        min_accepted_wrong_rows=10,
        min_physical_pairs=6,
        min_left_steps=5,
        min_checkpoints=2,
        min_targets=3,
        min_margin_buckets=2,
        min_success_drop_fraction=1.0,
        max_rows_per_pair_fraction=0.4,
        max_control_accepted_rows=0,
    )

    failed = {row["gate"] for row in gates if not row["passed"]}
    assert "accepted_wrong_physical_pairs" in failed
    assert decision_from_gates(gates) == "reject_duplicate_dominated_boundary_surface"


def test_run_writes_robustness_artifacts(tmp_path: Path):
    frame = pd.DataFrame(
        [
            _row(checkpoint_label="m102", target="brake", left_step=10, right_step=20),
            _row(checkpoint_label="m105", target="yaw", left_step=11, right_step=21, normal_margin=0.016),
            _row(checkpoint_label="m62", target="yaw", left_step=12, right_step=22, accepted=False),
        ]
    )
    source = tmp_path / "boundary_rows.csv"
    frame.to_csv(source, index=False)

    result = run_boundary_wrong_history_surface_robustness(
        boundary_rows_csv=source,
        control_checkpoint_label="m62",
        margin_bucket_width=0.01,
        min_accepted_wrong_rows=2,
        min_physical_pairs=2,
        min_left_steps=2,
        min_checkpoints=2,
        min_targets=2,
        min_margin_buckets=2,
        min_success_drop_fraction=1.0,
        max_rows_per_pair_fraction=0.6,
        max_control_accepted_rows=0,
        run_dir=tmp_path / "run",
    )

    assert result["decision"] == "admit_boundary_wrong_history_objective"
    assert (tmp_path / "run" / "summary.json").exists()
    assert (tmp_path / "run" / "robustness_gates.csv").exists()
