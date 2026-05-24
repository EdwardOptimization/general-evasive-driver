from autodrift.fresh_trajectory_boundary_sampler import classify_fresh_result, boundary_bucket


def test_boundary_bucket_assigns_terminal_and_safe_ranges():
    assert boundary_bucket(0.01, 0.02, 0.15, 0.50) == "terminal_cliff"
    assert boundary_bucket(0.10, 0.02, 0.15, 0.50) == "near_boundary"
    assert boundary_bucket(0.30, 0.02, 0.15, 0.50) == "wide_but_sensitive"
    assert boundary_bucket(0.90, 0.02, 0.15, 0.50) == "too_safe"


def test_classify_fresh_result_requires_history_rows_for_positive():
    result = classify_fresh_result(
        accepted_rows=100,
        trajectory_boundary_rows=100,
        history_action_critical_rows=0,
        prepass_rows=120,
        normal_failed_rejected=0,
        too_safe_rejected=0,
        unique_seeds=50,
        unique_step_buckets=6,
        unique_distance_buckets=6,
        max_seed_dominance=0.04,
        max_bucket_dominance=0.10,
        min_accepted_rows=80,
        min_trajectory_rows=50,
        min_history_rows=20,
        min_unique_seeds=30,
        min_unique_step_buckets=4,
        min_unique_distance_buckets=4,
        max_seed_dominance_threshold=0.08,
        max_bucket_dominance_threshold=0.25,
    )

    assert result == "history_insensitive"


def test_classify_fresh_result_accepts_diverse_history_sensitive_source():
    result = classify_fresh_result(
        accepted_rows=100,
        trajectory_boundary_rows=80,
        history_action_critical_rows=25,
        prepass_rows=120,
        normal_failed_rejected=5,
        too_safe_rejected=10,
        unique_seeds=50,
        unique_step_buckets=6,
        unique_distance_buckets=6,
        max_seed_dominance=0.04,
        max_bucket_dominance=0.10,
        min_accepted_rows=80,
        min_trajectory_rows=50,
        min_history_rows=20,
        min_unique_seeds=30,
        min_unique_step_buckets=4,
        min_unique_distance_buckets=4,
        max_seed_dominance_threshold=0.08,
        max_bucket_dominance_threshold=0.25,
    )

    assert result == "fresh_source_positive"


def test_classify_fresh_result_separates_empty_and_normal_failed():
    assert (
        classify_fresh_result(
            accepted_rows=0,
            trajectory_boundary_rows=0,
            history_action_critical_rows=0,
            prepass_rows=10,
            normal_failed_rejected=10,
            too_safe_rejected=0,
            unique_seeds=0,
            unique_step_buckets=0,
            unique_distance_buckets=0,
            max_seed_dominance=0.0,
            max_bucket_dominance=0.0,
            min_accepted_rows=80,
            min_trajectory_rows=50,
            min_history_rows=20,
            min_unique_seeds=30,
            min_unique_step_buckets=4,
            min_unique_distance_buckets=4,
            max_seed_dominance_threshold=0.08,
            max_bucket_dominance_threshold=0.25,
        )
        == "normal_failed_only"
    )
