"""Scenario generation and feasibility labels for emergency avoidance."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import sys

import numpy as np

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json


@dataclass(frozen=True)
class ObstacleScenarioConfig:
    speed_range: tuple[float, float] = (8.0, 16.0)
    mu_range: tuple[float, float] = (0.25, 1.15)
    obstacle_distance_range: tuple[float, float] = (16.0, 55.0)
    obstacle_half_width_range: tuple[float, float] = (0.45, 1.15)
    ego_half_width: float = 0.90
    safety_margin: float = 0.30
    brake_mu_fraction: float = 0.90
    conventional_lateral_mu_fraction: float = 0.42
    drift_lateral_mu_fraction: float = 0.85
    gravity: float = 9.81


@dataclass(frozen=True)
class ObstacleScenario:
    seed: int
    speed: float
    mu: float
    obstacle_distance: float
    obstacle_half_width: float
    required_lateral_offset: float
    time_to_obstacle: float
    aeb_stop_distance: float
    conventional_lateral_capacity: float
    drift_lateral_capacity: float
    label: str
    obstacle_lateral_offset: float = 0.0
    obstacle_lateral_velocity: float = 0.0
    predicted_lateral_offset_at_arrival: float = 0.0


def classify_obstacle_scenario(
    speed: float,
    mu: float,
    obstacle_distance: float,
    obstacle_half_width: float,
    config: ObstacleScenarioConfig | None = None,
    obstacle_lateral_offset: float = 0.0,
    obstacle_lateral_velocity: float = 0.0,
) -> ObstacleScenario:
    config = config or ObstacleScenarioConfig()
    speed = float(speed)
    mu = float(mu)
    obstacle_distance = float(obstacle_distance)
    obstacle_half_width = float(obstacle_half_width)
    obstacle_lateral_offset = float(obstacle_lateral_offset)
    obstacle_lateral_velocity = float(obstacle_lateral_velocity)
    collision_radius = config.ego_half_width + obstacle_half_width + config.safety_margin
    time_to_obstacle = obstacle_distance / max(speed, 1e-6)
    predicted_lateral_offset = obstacle_lateral_offset + obstacle_lateral_velocity * time_to_obstacle
    required_offset = max(collision_radius - abs(predicted_lateral_offset), 0.0)

    brake_accel = max(config.brake_mu_fraction * mu * config.gravity, 1e-6)
    aeb_stop_distance = speed**2 / (2.0 * brake_accel)
    conventional_lateral_capacity = 0.5 * config.conventional_lateral_mu_fraction * mu * config.gravity * time_to_obstacle**2
    drift_lateral_capacity = 0.5 * config.drift_lateral_mu_fraction * mu * config.gravity * time_to_obstacle**2

    if aeb_stop_distance <= obstacle_distance - config.safety_margin:
        label = "aeb_feasible"
    elif conventional_lateral_capacity >= required_offset:
        label = "aes_feasible"
    elif drift_lateral_capacity >= required_offset:
        label = "drift_required"
    else:
        label = "unavoidable"

    return ObstacleScenario(
        seed=-1,
        speed=speed,
        mu=mu,
        obstacle_distance=obstacle_distance,
        obstacle_half_width=obstacle_half_width,
        required_lateral_offset=required_offset,
        time_to_obstacle=time_to_obstacle,
        aeb_stop_distance=aeb_stop_distance,
        conventional_lateral_capacity=conventional_lateral_capacity,
        drift_lateral_capacity=drift_lateral_capacity,
        label=label,
        obstacle_lateral_offset=obstacle_lateral_offset,
        obstacle_lateral_velocity=obstacle_lateral_velocity,
        predicted_lateral_offset_at_arrival=predicted_lateral_offset,
    )


def sample_obstacle_scenario(seed: int, config: ObstacleScenarioConfig | None = None) -> ObstacleScenario:
    config = config or ObstacleScenarioConfig()
    rng = np.random.default_rng(seed)
    scenario = classify_obstacle_scenario(
        speed=float(rng.uniform(*config.speed_range)),
        mu=float(rng.uniform(*config.mu_range)),
        obstacle_distance=float(rng.uniform(*config.obstacle_distance_range)),
        obstacle_half_width=float(rng.uniform(*config.obstacle_half_width_range)),
        config=config,
    )
    return ObstacleScenario(seed=seed, **{key: value for key, value in asdict(scenario).items() if key != "seed"})


def sample_obstacle_scenarios(
    count: int,
    seed: int = 7,
    config: ObstacleScenarioConfig | None = None,
    require_aeb_infeasible: bool = False,
) -> list[ObstacleScenario]:
    config = config or ObstacleScenarioConfig()
    scenarios: list[ObstacleScenario] = []
    candidate_seed = int(seed)
    max_attempts = max(1000, count * 100)
    attempts = 0
    while len(scenarios) < count and attempts < max_attempts:
        scenario = sample_obstacle_scenario(candidate_seed, config=config)
        candidate_seed += 1
        attempts += 1
        if require_aeb_infeasible and scenario.label == "aeb_feasible":
            continue
        scenarios.append(scenario)
    if len(scenarios) < count:
        raise RuntimeError(f"sampled only {len(scenarios)} scenarios after {attempts} attempts")
    return scenarios


def label_counts(scenarios: list[ObstacleScenario]) -> dict[str, int]:
    labels = ["aeb_feasible", "aes_feasible", "drift_required", "unavoidable"]
    return {label: sum(1 for scenario in scenarios if scenario.label == label) for label in labels}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate emergency obstacle avoidance scenario labels.")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--require-aeb-infeasible", action="store_true")
    parser.add_argument("--run-dir", default=None)
    args = parser.parse_args()

    config = ObstacleScenarioConfig()
    scenarios = sample_obstacle_scenarios(
        count=args.count,
        seed=args.seed,
        config=config,
        require_aeb_infeasible=args.require_aeb_infeasible,
    )
    rows = [asdict(scenario) for scenario in scenarios]
    run_dir = make_run_dir(prefix="scenarios_m5", seed=args.seed) if args.run_dir is None else args.run_dir
    write_csv_rows(f"{run_dir}/scenarios.csv", rows)
    write_json(
        f"{run_dir}/summary.json",
        {
            "command": sys.argv,
            "config": config,
            "count": len(scenarios),
            "label_counts": label_counts(scenarios),
            "require_aeb_infeasible": args.require_aeb_infeasible,
        },
    )
    print(f"run_dir={run_dir}")
    print(f"label_counts={label_counts(scenarios)}")


if __name__ == "__main__":
    main()
