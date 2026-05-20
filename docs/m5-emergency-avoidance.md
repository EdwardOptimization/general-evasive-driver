# M5 Emergency Avoidance

Last updated: 2026-05-20

## Goal

M5 introduces obstacle-avoidance scenarios where ordinary AEB may be unable to
stop before the obstacle. The first implementation step is a reproducible
scenario layer that labels cases before RL training starts.

## Scenario Labels

The scenario generator computes a conservative feasibility label from speed,
friction, obstacle distance, obstacle width, and simple acceleration envelopes:

- `aeb_feasible`: braking distance fits before the obstacle;
- `aes_feasible`: AEB is infeasible, but conventional lateral acceleration can
  clear the obstacle;
- `drift_required`: conventional AES is insufficient, but a high-sideslip
  lateral envelope can clear the obstacle;
- `unavoidable`: neither braking nor the high-sideslip lateral envelope clears
  the obstacle.

These are not final safety proofs. They are engineering labels for fixed-seed
benchmark buckets, so later RL and baseline policies are compared on the same
scenario classes.

## Implemented Infrastructure

Scenario module:

```text
src/autodrift/scenarios.py
```

Environment integration:

```text
DriftEnvConfig.obstacle
ObstacleTaskConfig
```

When enabled, the environment:

- samples and labels an obstacle scenario at reset;
- can reject `aeb_feasible` samples with `require_aeb_infeasible=true`;
- appends obstacle-relative features to the policy observation;
- reports `obstacle_label`, `collision`, and `min_obstacle_clearance` in
  episode info and benchmark CSVs;
- writes `obstacle_label_summary.csv` from benchmark runs.

Command:

```bash
PYTHONPATH=src python -m autodrift.scenarios \
  --count 50 \
  --seed 7 \
  --require-aeb-infeasible \
  --run-dir runs/scenarios_m5_smoke
```

Smoke result:

| label | count |
| --- | ---: |
| aeb_feasible | 0 |
| aes_feasible | 27 |
| drift_required | 19 |
| unavoidable | 4 |

Artifacts:

```text
runs/scenarios_m5_smoke/scenarios.csv
runs/scenarios_m5_smoke/summary.json
```

The command-line entry point is also exposed as:

```bash
autodrift-scenarios
```

## Environment Smoke

Config:

```text
configs/m5_obstacle_smoke_eval.json
```

Command:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 20 \
  --policies heuristic \
  --env-config configs/m5_obstacle_smoke_eval.json \
  --run-dir runs/benchmark_m5_obstacle_env_smoke
```

Overall result:

| policy | episodes | success_rate | collision_rate | min_obstacle_clearance_mean |
| --- | ---: | ---: | ---: | ---: |
| heuristic | 20 | 0.000 | 0.950 | 1.594 |

Label bucket result:

| obstacle_label | episodes | success_rate | collision_rate | min_obstacle_clearance_mean |
| --- | ---: | ---: | ---: | ---: |
| drift_required | 4 | 0.000 | 1.000 | 1.598 |
| unavoidable | 16 | 0.000 | 0.938 | 1.593 |

Interpretation:

- The M5 environment path now produces AEB-infeasible obstacle scenarios and
  benchmark label buckets.
- The existing circular-tracking heuristic is not an avoidance baseline. It
  collides in nearly every AEB-infeasible smoke scenario, which is the expected
  negative baseline.
- The next M5 step is to add explicit AEB-only and heuristic AES policies, then
  train/evaluate RL on the same fixed obstacle-label buckets.

## Baseline Smoke

Implemented policy names:

```text
aeb
aes_heuristic
```

Benchmark command:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 20 \
  --policies aeb aes_heuristic heuristic \
  --env-config configs/m5_obstacle_smoke_eval.json \
  --run-dir runs/benchmark_m5_baselines_smoke
```

Overall result:

| policy | episodes | success_rate | collision_rate | min_obstacle_clearance_mean |
| --- | ---: | ---: | ---: | ---: |
| aeb | 20 | 0.000 | 1.000 | 1.649 |
| aes_heuristic | 20 | 0.000 | 0.800 | 1.755 |
| heuristic | 20 | 0.000 | 0.950 | 1.594 |

Label bucket result:

| policy | obstacle_label | episodes | success_rate | collision_rate | min_obstacle_clearance_mean |
| --- | --- | ---: | ---: | ---: | ---: |
| aeb | drift_required | 4 | 0.000 | 1.000 | 1.649 |
| aeb | unavoidable | 16 | 0.000 | 1.000 | 1.648 |
| aes_heuristic | drift_required | 4 | 0.000 | 0.500 | 2.075 |
| aes_heuristic | unavoidable | 16 | 0.000 | 0.875 | 1.675 |
| heuristic | drift_required | 4 | 0.000 | 1.000 | 1.598 |
| heuristic | unavoidable | 16 | 0.000 | 0.938 | 1.593 |

Interpretation:

- The AEB-only baseline correctly fails in AEB-infeasible scenarios.
- The heuristic AES baseline improves clearance and collision rate versus AEB,
  but still has zero success on this smoke set.
- This is now a valid fixed-seed M5 baseline gate for the first RL obstacle
  policy.

## Next Steps

M5 is still incomplete. The next implementation work is:

- train/evaluate RL on fixed `aes_feasible`, `drift_required`, and
  `unavoidable` buckets;
- keep AEB-infeasible filtering explicit in every M5 benchmark manifest.
