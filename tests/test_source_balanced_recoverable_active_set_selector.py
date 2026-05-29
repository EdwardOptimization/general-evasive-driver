from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.source_balanced_recoverable_active_set_selector import (
    build_summary,
    run_source_balanced_recoverable_active_set_selector,
    select_source_balanced_rows,
)


def _row(index: int, *, family: str, window: str, strong: bool = True, collision_flips: int = 0, success_flips: int = 0):
    return {
        "anchor_id": f"{family}-{window}-{index}",
        "calibration_id": f"calib-{index}",
        "source_row_id": f"source-{index}",
        "source_family": family,
        "task_family": "T5",
        "seed": str(1000 + index),
        "mode_name": "mode",
        "anchor_window": window,
        "anchor_step": str(index),
        "reveal_step": "20",
        "decision_step": "50",
        "phase": "pre_reveal",
        "normal_replay_status": "ok",
        "normal_terminal_margin": "0.05",
        "normal_success": "True",
        "normal_collision": "False",
        "normal_obstacle_completed": "True",
        "normal_terminal_reason": "obstacle_completed",
        "triage_label": "strong_recoverable_boundary" if strong else "recoverable_boundary",
        "recoverable_boundary": "True",
        "strong_recoverable_boundary": str(strong),
        "max_abs_terminal_margin_gap": "0.08" if strong else "0.03",
        "success_flip_count": str(success_flips),
        "collision_flip_count": str(collision_flips),
        "best_override": "steer_left",
        "best_hold_steps": "8",
    }


def _balanced_rows() -> list[dict[str, str]]:
    families = [f"family_{index}" for index in range(5)]
    windows = ["reveal", "reveal_plus_4", "decision_minus_24", "decision_minus_16", "decision"]
    rows: list[dict[str, str]] = []
    for index in range(60):
        rows.append(
            _row(
                index,
                family=families[index % len(families)],
                window=windows[index % len(windows)],
                strong=index < 36,
                collision_flips=1 if index < 12 else 0,
                success_flips=1 if index < 12 else 0,
            )
        )
    return rows


def test_selector_enforces_source_window_caps_and_coverage():
    rows = _balanced_rows()

    selected = select_source_balanced_rows(rows, max_per_source_family=8, max_per_anchor_window=9, min_selected_rows=35)

    assert len(selected) == 35
    assert len({row["source_family"] for row in selected}) == 5
    assert len({row["anchor_window"] for row in selected}) == 5
    assert max(sum(1 for row in selected if row["source_family"] == family) for family in {row["source_family"] for row in selected}) <= 8
    assert max(sum(1 for row in selected if row["anchor_window"] == window) for window in {row["anchor_window"] for row in selected}) <= 9


def test_summary_reports_flip_anchor_gate_separately_from_variant_counts():
    rows = _balanced_rows()
    for index, row in enumerate(rows):
        row["collision_flip_count"] = "3" if index < 3 else "0"
        row["success_flip_count"] = "3" if index < 3 else "0"
    selected = select_source_balanced_rows(rows)
    rejected = [row for row in rows if row["anchor_id"] not in {selected_row["anchor_id"] for selected_row in selected}]

    summary = build_summary(
        input_dir=Path("input"),
        input_summary={"result_class": "synthetic"},
        candidates=rows,
        selected_rows=selected,
        rejected_rows=rejected,
        local_rows=[],
    )

    assert summary["selected_collision_flip_variant_count"] >= summary["selected_collision_flip_anchor_count"]
    assert summary["input_flip_anchor_gate_feasible"] is False
    assert summary["passes_public_selector_gates"] is False
    assert "input_flip_anchor_gate_infeasible" in summary["failed_public_selector_gates"]


def test_run_selector_writes_artifacts(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    rows = _balanced_rows()
    write_csv_rows(input_dir / "recoverable_active_anchor_rows.csv", rows)
    write_csv_rows(input_dir / "local_hold_rows.csv", [])
    write_json(input_dir / "summary.json", {"result_class": "synthetic_generator"})

    summary = run_source_balanced_recoverable_active_set_selector(output_dir, input_dir=input_dir)

    assert summary["selected_recoverable_anchor_count"] == 40
    assert summary["selected_source_family_count"] == 5
    assert summary["selected_window_count"] == 5
    assert (output_dir / "selected_active_anchor_rows.csv").exists()
    assert (output_dir / "rejected_active_anchor_rows.csv").exists()
    assert (output_dir / "selector_source_family_summary.csv").exists()
    assert (output_dir / "selector_window_summary.csv").exists()
    assert (output_dir / "selector_guardrail_summary.csv").exists()
    assert (output_dir / "summary.json").exists()
