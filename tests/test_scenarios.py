from autodrift.scenarios import (
    ObstacleScenarioConfig,
    classify_obstacle_scenario,
    label_counts,
    sample_obstacle_scenarios,
)


def test_obstacle_scenario_labels_aeb_feasible_case():
    scenario = classify_obstacle_scenario(speed=8.0, mu=1.0, obstacle_distance=60.0, obstacle_half_width=0.8)

    assert scenario.label == "aeb_feasible"
    assert scenario.aeb_stop_distance < scenario.obstacle_distance


def test_obstacle_scenario_labels_drift_required_case():
    config = ObstacleScenarioConfig(
        brake_mu_fraction=0.9,
        conventional_lateral_mu_fraction=0.35,
        drift_lateral_mu_fraction=0.90,
    )
    scenario = classify_obstacle_scenario(
        speed=19.0,
        mu=0.9,
        obstacle_distance=21.0,
        obstacle_half_width=1.0,
        config=config,
    )

    assert scenario.label == "drift_required"
    assert scenario.aeb_stop_distance > scenario.obstacle_distance
    assert scenario.conventional_lateral_capacity < scenario.required_lateral_offset
    assert scenario.drift_lateral_capacity >= scenario.required_lateral_offset


def test_obstacle_scenario_rederives_label_with_lateral_motion():
    config = ObstacleScenarioConfig(
        brake_mu_fraction=0.9,
        conventional_lateral_mu_fraction=0.42,
        drift_lateral_mu_fraction=0.85,
    )
    static = classify_obstacle_scenario(
        speed=20.0,
        mu=0.5,
        obstacle_distance=16.0,
        obstacle_half_width=1.0,
        config=config,
    )
    moving_away = classify_obstacle_scenario(
        speed=20.0,
        mu=0.5,
        obstacle_distance=16.0,
        obstacle_half_width=1.0,
        config=config,
        obstacle_lateral_offset=0.0,
        obstacle_lateral_velocity=5.0,
    )

    assert static.label == "unavoidable"
    assert moving_away.label == "aes_feasible"
    assert moving_away.obstacle_lateral_velocity == 5.0
    assert moving_away.predicted_lateral_offset_at_arrival == 4.0
    assert moving_away.required_lateral_offset == 0.0


def test_obstacle_sampler_can_filter_aeb_feasible_scenarios():
    scenarios = sample_obstacle_scenarios(count=20, seed=5, require_aeb_infeasible=True)
    counts = label_counts(scenarios)

    assert counts["aeb_feasible"] == 0
    assert sum(counts.values()) == 20
