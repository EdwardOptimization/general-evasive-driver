# M3223 Review: B1 Moving-Obstacle Kinematics Smoke

Status: accepted as an auxiliary env-engineering smoke.

## Findings

No blocking issues found in the B1 smoke artifact.

The implementation is behind a non-default `ObstacleTaskConfig.motion_mode`.
The default static obstacle behavior and obs72 shape are preserved. Legacy
`obstacle_relative_velocity_mode="zero"` remains exact-zero for obstacle
relative-velocity slots, including moving-obstacle scenarios.

The full smoke artifact reports all preregistered gates passing:
zero-relvel violations 0, moving body-y delta min 0.6053 m, ego rel-velocity
non-zero, dynamic label rows 1312/1312, and deterministic replay failures 0.

The label re-derivation is correctly scoped: it records the obstacle lateral
velocity and predicted lateral offset at arrival, then reuses the existing
AEB/AES/drift/unavoidable hierarchy. This is an env-label smoke, not a
feasibility proof for a controller.

## Decision

Accept M3223 as complete. Mark B1 DONE. Future moving-obstacle measurements
must still be preregistered separately before any training or outcome claim.

## Checks

- `make research-validate` in pending state
- `env PYTHONPATH=src OMP_NUM_THREADS=1 python -m pytest -q tests/test_scenarios.py tests/test_config.py tests/test_env.py`
- `env PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/moving_obstacle_smoke.py --quick`
- `env PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/moving_obstacle_smoke.py`
