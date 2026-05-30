import pytest

from autodrift.seed_repair_completion import (
    SEED_REPAIR_PROVENANCE_FIELDS,
    SeedRepairPlan,
    augment_episode_rows_with_seed_repair,
    require_single_failure_row,
    select_seed_repair_plan,
    seed_repair_provenance_rows,
)


def test_select_seed_repair_plan_uses_nearest_lower_seed_tie_break() -> None:
    rows = [
        {
            "workload_id": "m1728-s4-02::L2_window_13_current_tiled",
            "seed_role": "exact",
            "eval_seed": "175761",
            "seed_offset": "0",
            "reset_success": "False",
            "sampled_obstacle_label": "",
        },
        {
            "workload_id": "m1728-s4-02::L2_window_13_current_tiled",
            "seed_role": "neighbor",
            "eval_seed": "175762",
            "seed_offset": "1",
            "reset_success": "True",
            "sampled_obstacle_label": "unavoidable",
        },
        {
            "workload_id": "m1728-s4-02::L2_window_13_current_tiled",
            "seed_role": "neighbor",
            "eval_seed": "175760",
            "seed_offset": "-1",
            "reset_success": "True",
            "sampled_obstacle_label": "unavoidable",
        },
    ]

    plan = select_seed_repair_plan(rows)

    assert plan.replacement_eval_seed == 175760
    assert plan.replacement_seed_offset == -1
    assert plan.seed_repair_rule == "nearest_successful_neighbor_tie_lower"


def test_require_single_failure_row_rejects_unexpected_workload() -> None:
    with pytest.raises(ValueError, match="unexpected failure workload_id"):
        require_single_failure_row([{"workload_id": "other"}])


def test_augment_episode_rows_adds_provenance_without_mutating_copied_rows() -> None:
    source_rows = [{"workload_id": "w0", "sampled_obstacle_label": "unavoidable", "return": 1.0}]
    repaired_row = {
        "workload_id": "m1728-s4-02::L2_window_13_current_tiled",
        "sampled_obstacle_label": "unavoidable",
        "return": 2.0,
    }
    failure_row = {
        "workload_id": "m1728-s4-02::L2_window_13_current_tiled",
        "error_type": "RuntimeError",
        "error_message": "failed to sample an obstacle scenario matching the configured filters",
    }
    plan = SeedRepairPlan()

    rows = augment_episode_rows_with_seed_repair(
        source_episode_rows=source_rows,
        repaired_row=repaired_row,
        failure_row=failure_row,
        plan=plan,
    )

    assert rows[0]["seed_repair_applied"] is False
    assert rows[0]["replacement_eval_seed"] == ""
    assert rows[1]["seed_repair_applied"] is True
    assert rows[1]["original_eval_seed"] == 175761
    assert rows[1]["replacement_eval_seed"] == 175760
    assert rows[1]["replacement_seed_offset"] == -1
    assert rows[1]["original_failure_error_type"] == "RuntimeError"
    for field in SEED_REPAIR_PROVENANCE_FIELDS:
        assert field in rows[0]
        assert field in rows[1]


def test_augment_episode_rows_rejects_wrong_sampled_label() -> None:
    with pytest.raises(ValueError, match="sampled_obstacle_label"):
        augment_episode_rows_with_seed_repair(
            source_episode_rows=[],
            repaired_row={
                "workload_id": "m1728-s4-02::L2_window_13_current_tiled",
                "sampled_obstacle_label": "aes_feasible",
            },
            failure_row={"workload_id": "m1728-s4-02::L2_window_13_current_tiled"},
            plan=SeedRepairPlan(),
        )


def test_seed_repair_provenance_rows_preserve_original_failure() -> None:
    rows = seed_repair_provenance_rows(
        SeedRepairPlan(),
        {
            "workload_id": "m1728-s4-02::L2_window_13_current_tiled",
            "error_type": "RuntimeError",
            "error_message": "failed to sample",
        },
    )

    assert rows == [
        {
            "workload_id": "m1728-s4-02::L2_window_13_current_tiled",
            "seed_repair_applied": True,
            "seed_repair_source": "m1758_single_sampling_failure_reset_only_probe",
            "seed_repair_rule": "nearest_successful_neighbor_tie_lower",
            "original_eval_seed": 175761,
            "replacement_eval_seed": 175760,
            "replacement_seed_offset": -1,
            "expected_sampled_obstacle_label": "unavoidable",
            "original_failure_error_type": "RuntimeError",
            "original_failure_error_message": "failed to sample",
        }
    ]
