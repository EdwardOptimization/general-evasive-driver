from autodrift.single_sampling_failure_reset_probe import (
    classify_probe_rows,
    neighboring_seed_schedule,
)


def test_neighboring_seed_schedule_starts_with_exact_seed() -> None:
    assert neighboring_seed_schedule(exact_seed=10, neighbor_radius=2) == [
        (10, "exact", 0),
        (9, "neighbor", -1),
        (11, "neighbor", 1),
        (8, "neighbor", -2),
        (12, "neighbor", 2),
    ]


def test_classify_seed_fragile_when_exact_fails_but_neighbor_succeeds() -> None:
    rows = [
        {"seed_role": "exact", "reset_success": False},
        {"seed_role": "neighbor", "reset_success": False},
        {"seed_role": "neighbor", "reset_success": True},
    ]

    assert classify_probe_rows(rows, neighbor_radius=2) == "seed_fragile_but_feasible"


def test_classify_spec_filter_infeasible_when_full_neighbor_window_fails() -> None:
    rows = [
        {"seed_role": "exact", "reset_success": False},
        {"seed_role": "neighbor", "reset_success": False},
        {"seed_role": "neighbor", "reset_success": False},
    ]

    assert classify_probe_rows(rows, neighbor_radius=1) == "spec_filter_infeasible"


def test_classify_inconclusive_when_exact_seed_succeeds() -> None:
    rows = [
        {"seed_role": "exact", "reset_success": True},
        {"seed_role": "neighbor", "reset_success": True},
    ]

    assert classify_probe_rows(rows, neighbor_radius=1) == "probe_inconclusive"
