"""Configuration builders for AutoDrift experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any

from autodrift.dynamics import RandomizationConfig
from autodrift.env import (
    DriftEnvConfig,
    FrictionStepConfig,
    ObservationDegradationConfig,
    ObstacleTaskConfig,
    WarmupGateConfig,
)


def _tuple2(value: Any) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"expected a two-element range, got {value!r}")
    return float(value[0]), float(value[1])


def build_randomization_config(data: dict[str, Any] | None = None) -> RandomizationConfig:
    values = asdict(RandomizationConfig())
    for key, value in (data or {}).items():
        if key not in values:
            raise ValueError(f"unknown randomization config key: {key}")
        values[key] = _tuple2(value)
    return RandomizationConfig(**values)


def build_env_config(data: dict[str, Any] | None = None) -> DriftEnvConfig:
    values = asdict(DriftEnvConfig())
    values["randomization"] = asdict(RandomizationConfig())
    values["friction_step"] = asdict(FrictionStepConfig())
    values["obstacle"] = asdict(ObstacleTaskConfig())
    values["warmup_gate"] = asdict(WarmupGateConfig())
    for key, value in (data or {}).items():
        if key not in values:
            raise ValueError(f"unknown env config key: {key}")
        if key == "randomization":
            randomization = values["randomization"].copy()
            for rand_key, rand_value in value.items():
                if rand_key not in randomization:
                    raise ValueError(f"unknown randomization config key: {rand_key}")
                randomization[rand_key] = _tuple2(rand_value)
            values["randomization"] = randomization
        elif key == "friction_step":
            friction_step = values["friction_step"].copy()
            for step_key, step_value in value.items():
                if step_key not in friction_step:
                    raise ValueError(f"unknown friction_step config key: {step_key}")
                if step_key.endswith("_range"):
                    if step_key == "step_range":
                        step_range = _tuple2(step_value)
                        friction_step[step_key] = (int(step_range[0]), int(step_range[1]))
                    else:
                        friction_step[step_key] = _tuple2(step_value)
                else:
                    friction_step[step_key] = step_value
            values["friction_step"] = friction_step
        elif key == "obstacle":
            obstacle = values["obstacle"].copy()
            for obstacle_key, obstacle_value in value.items():
                if obstacle_key not in obstacle:
                    raise ValueError(f"unknown obstacle config key: {obstacle_key}")
                if obstacle_key == "allowed_labels":
                    obstacle[obstacle_key] = tuple(str(label) for label in obstacle_value)
                elif obstacle_key.endswith("_range"):
                    obstacle[obstacle_key] = _tuple2(obstacle_value)
                else:
                    obstacle[obstacle_key] = obstacle_value
            values["obstacle"] = obstacle
        elif key == "warmup_gate":
            warmup_gate = values["warmup_gate"].copy()
            for gate_key, gate_value in value.items():
                if gate_key not in warmup_gate:
                    raise ValueError(f"unknown warmup_gate config key: {gate_key}")
                if gate_key.endswith("_range"):
                    warmup_gate[gate_key] = _tuple2(gate_value)
                else:
                    warmup_gate[gate_key] = gate_value
            values["warmup_gate"] = warmup_gate
        elif key == "observation_degradation":
            if value is None:
                values[key] = None
            else:
                if not isinstance(value, dict):
                    raise ValueError("observation_degradation must be a mapping or null")
                known_keys = {field.name for field in fields(ObservationDegradationConfig)}
                for degradation_key in value:
                    if degradation_key not in known_keys:
                        raise ValueError(f"unknown observation_degradation config key: {degradation_key}")
                values[key] = dict(value)
        elif key.endswith("_range"):
            values[key] = _tuple2(value)
        else:
            values[key] = value
    values["randomization"] = build_randomization_config(values["randomization"])
    values["friction_step"] = FrictionStepConfig(**values["friction_step"])
    values["obstacle"] = ObstacleTaskConfig(**values["obstacle"])
    values["warmup_gate"] = WarmupGateConfig(**values["warmup_gate"])
    if values["observation_degradation"] is not None:
        values["observation_degradation"] = ObservationDegradationConfig(**values["observation_degradation"])
    return DriftEnvConfig(**values)


def env_config_to_dict(config: DriftEnvConfig) -> dict[str, Any]:
    return asdict(config)


def merge_env_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key == "randomization":
            randomization = dict(merged.get("randomization", {}))
            randomization.update(value)
            merged["randomization"] = randomization
        elif key == "friction_step":
            friction_step = dict(merged.get("friction_step", {}))
            friction_step.update(value)
            merged["friction_step"] = friction_step
        elif key == "obstacle":
            obstacle = dict(merged.get("obstacle", {}))
            obstacle.update(value)
            merged["obstacle"] = obstacle
        elif key == "warmup_gate":
            warmup_gate = dict(merged.get("warmup_gate", {}))
            warmup_gate.update(value)
            merged["warmup_gate"] = warmup_gate
        elif key == "observation_degradation":
            if value is None:
                merged["observation_degradation"] = None
            else:
                observation_degradation = dict(merged.get("observation_degradation") or {})
                observation_degradation.update(value)
                merged["observation_degradation"] = observation_degradation
        else:
            merged[key] = value
    return merged


@dataclass(frozen=True)
class CurriculumStage:
    name: str
    until_step: int
    env_config: DriftEnvConfig


def build_curriculum(
    base_env_data: dict[str, Any],
    stages_data: list[dict[str, Any]] | None,
) -> list[CurriculumStage]:
    stages: list[CurriculumStage] = []
    for index, stage_data in enumerate(stages_data or []):
        if "until_step" not in stage_data:
            raise ValueError(f"curriculum stage {index} is missing until_step")
        stage_env_data = merge_env_config(base_env_data, stage_data.get("env", {}))
        stages.append(
            CurriculumStage(
                name=str(stage_data.get("name", f"stage_{index}")),
                until_step=int(stage_data["until_step"]),
                env_config=build_env_config(stage_env_data),
            )
        )
    stages.sort(key=lambda stage: stage.until_step)
    return stages


def env_config_for_step(
    base_env_config: DriftEnvConfig,
    curriculum: list[CurriculumStage],
    step: int,
) -> tuple[DriftEnvConfig, str]:
    for stage in curriculum:
        if step < stage.until_step:
            return stage.env_config, stage.name
    return base_env_config, "base"
