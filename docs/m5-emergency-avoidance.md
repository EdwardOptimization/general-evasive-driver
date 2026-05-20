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

For obstacle tasks, success is defined as passing the obstacle without
collision while still inside the track. `finish_on_pass=true` ends the episode
with `truncated=True` and `terminated=False` after the ego vehicle has passed
the obstacle by the configured distance. This avoids treating a completed
emergency avoidance maneuver as a failure just because the vehicle did not keep
tracking the circle for the rest of an 800-step episode.

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

## First RL Training Template

Config:

```text
configs/ppo_m5_obstacle_avoidance.json
```

The historical M5 run started from the M2 circular-drift checkpoint using a
partial first-layer expansion path. That compatibility path has been removed.
Current obstacle-driver runs must train from scratch or load a strict
same-contract checkpoint.

Smoke command:

```bash
PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m5_obstacle_avoidance.json \
  --init-checkpoint runs/ppo_circle_m2_seed113_recover2/checkpoint.pt \
  --total-steps 512 \
  --eval-episodes 1 \
  --run-dir runs/ppo_m5_obstacle_seed83_smoke
```

Smoke result:

```text
loaded_init_checkpoint=... load_mode=partial_input_expand
training_device=cuda num_envs=16 curriculum_stage=aes_feasible_wide
```

The 512-step smoke was expected to fail behaviorally; its purpose was to verify
that M5 obstacle observations, AEB-infeasible sampling, checkpoint expansion,
and the PPO loop worked together. The checkpoint-expansion portion is historical
only.

## First RL Training Attempt

Command:

```bash
PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m5_obstacle_avoidance.json \
  --init-checkpoint runs/ppo_circle_m2_seed113_recover2/checkpoint.pt \
  --run-dir runs/ppo_m5_obstacle_seed83
```

Benchmark:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 100 \
  --policies aeb aes_heuristic heuristic checkpoint \
  --checkpoint runs/ppo_m5_obstacle_seed83/checkpoint.pt \
  --env-config configs/m5_obstacle_smoke_eval.json \
  --run-dir runs/benchmark_ppo_m5_obstacle_seed83_100eval
```

Overall result:

| policy | episodes | success_rate | collision_rate | return_mean | min_obstacle_clearance_mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| aeb | 100 | 0.000 | 0.960 | 0.26 | 1.603 |
| aes_heuristic | 100 | 0.000 | 0.840 | -17.37 | 1.686 |
| heuristic | 100 | 0.000 | 0.910 | 23.96 | 1.657 |
| checkpoint | 100 | 0.010 | 0.710 | 105.29 | 1.872 |

Label bucket result:

| policy | obstacle_label | episodes | success_rate | collision_rate | min_obstacle_clearance_mean |
| --- | --- | ---: | ---: | ---: | ---: |
| checkpoint | aes_feasible | 6 | 0.000 | 0.000 | 3.539 |
| checkpoint | drift_required | 22 | 0.045 | 0.091 | 2.194 |
| checkpoint | unavoidable | 72 | 0.000 | 0.958 | 1.634 |
| aeb | aes_feasible | 6 | 0.000 | 0.667 | 1.557 |
| aeb | drift_required | 22 | 0.000 | 0.909 | 1.630 |
| aeb | unavoidable | 72 | 0.000 | 1.000 | 1.599 |

Interpretation:

- The first M5 RL policy is not a solved avoidance controller. Overall success
  is only `0.010`.
- It does learn a useful partial behavior: collision rate drops from AEB's
  `0.960` to `0.710`, and it avoids all collisions in the small `aes_feasible`
  bucket.
- The main failure mode changes from pure collision to post-avoidance
  termination/off-track behavior. The next iteration should reward obstacle
  clearance and road recovery separately, and should benchmark `aes_feasible`
  and `drift_required` buckets with enough samples instead of letting
  `unavoidable` dominate the evaluation set.

## Pass-Semantics Re-Evaluation

After adding `finish_on_pass=true`, the same first M5 checkpoint was
re-evaluated with obstacle pass completion semantics.

Command:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 100 \
  --policies aeb aes_heuristic heuristic checkpoint \
  --checkpoint runs/ppo_m5_obstacle_seed83/checkpoint.pt \
  --env-config configs/m5_obstacle_smoke_eval.json \
  --run-dir runs/benchmark_ppo_m5_obstacle_seed83_pass_100eval
```

Overall result:

| policy | episodes | success_rate | collision_rate | obstacle_completion_rate | min_obstacle_clearance_mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| aeb | 100 | 0.040 | 0.960 | 0.040 | 1.603 |
| aes_heuristic | 100 | 0.160 | 0.840 | 0.160 | 1.686 |
| heuristic | 100 | 0.090 | 0.910 | 0.090 | 1.657 |
| checkpoint | 100 | 0.290 | 0.710 | 0.290 | 1.872 |

Label bucket result:

| policy | obstacle_label | episodes | success_rate | collision_rate | obstacle_completion_rate |
| --- | --- | ---: | ---: | ---: | ---: |
| checkpoint | aes_feasible | 6 | 1.000 | 0.000 | 1.000 |
| checkpoint | drift_required | 22 | 0.909 | 0.091 | 0.909 |
| checkpoint | unavoidable | 72 | 0.042 | 0.958 | 0.042 |
| aeb | aes_feasible | 6 | 0.333 | 0.667 | 0.333 |
| aeb | drift_required | 22 | 0.091 | 0.909 | 0.091 |
| aeb | unavoidable | 72 | 0.000 | 1.000 | 0.000 |

Interpretation:

- The RL checkpoint solves most avoidable scenarios in this seed set: `1.000`
  success on `aes_feasible` and `0.909` on `drift_required`.
- Overall success remains low because `unavoidable` dominates the sampled
  distribution. A final M5 gate should report avoidable and unavoidable buckets
  separately, not collapse them into one headline number.
- The next change should add label-filtered or balanced M5 benchmark configs so
  RL is judged on the cases that the scenario model says are physically
  avoidable.

## Label-Filtered M5 Benchmarks

Evaluation configs:

```text
configs/m5_obstacle_avoidable_eval.json
configs/m5_obstacle_drift_required_eval.json
```

The avoidable config filters to:

```text
allowed_labels = ["aes_feasible", "drift_required"]
```

The drift-required config filters to:

```text
allowed_labels = ["drift_required"]
```

Avoidable benchmark:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 100 \
  --policies aeb aes_heuristic heuristic checkpoint \
  --checkpoint runs/ppo_m5_obstacle_seed83/checkpoint.pt \
  --env-config configs/m5_obstacle_avoidable_eval.json \
  --run-dir runs/benchmark_ppo_m5_obstacle_seed83_avoidable_100eval
```

Overall result:

| policy | episodes | success_rate | collision_rate | obstacle_completion_rate | min_obstacle_clearance_mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| aeb | 100 | 0.080 | 0.920 | 0.080 | 1.578 |
| aes_heuristic | 100 | 0.500 | 0.500 | 0.500 | 1.853 |
| heuristic | 100 | 0.240 | 0.760 | 0.240 | 1.730 |
| checkpoint | 100 | 0.860 | 0.140 | 0.860 | 2.252 |

Drift-required benchmark:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 100 \
  --policies aeb aes_heuristic heuristic checkpoint \
  --checkpoint runs/ppo_m5_obstacle_seed83/checkpoint.pt \
  --env-config configs/m5_obstacle_drift_required_eval.json \
  --run-dir runs/benchmark_ppo_m5_obstacle_seed83_drift_required_100eval
```

Result:

| policy | episodes | success_rate | collision_rate | obstacle_completion_rate | min_obstacle_clearance_mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| aeb | 100 | 0.050 | 0.950 | 0.050 | 1.577 |
| aes_heuristic | 100 | 0.500 | 0.500 | 0.500 | 1.865 |
| heuristic | 100 | 0.190 | 0.810 | 0.190 | 1.669 |
| checkpoint | 100 | 0.860 | 0.140 | 0.860 | 2.180 |

Interpretation:

- M5 first pass is now successful on the benchmark bucket that matters most for
  the project objective: `drift_required` AEB-infeasible scenarios.
- The RL policy beats AEB-only, heuristic AES, and the original tracking
  heuristic on success rate, collision rate, and minimum clearance.
- `unavoidable` remains separated as a diagnostic bucket and should not be
  counted as a failure of an avoidance policy unless the scenario-label model is
  changed.
- Remaining M5 work is robustness: more seeds, balanced label sampling, richer
  obstacle geometry, and eventually replacing the simple feasibility-label
  model with a stronger planner or NMPC baseline.

## Next Steps

M5 first pass is complete. The next implementation work is:

- expand benchmark seeds and obstacle geometries;
- keep AEB-infeasible filtering explicit in every M5 benchmark manifest;
- add model-based baselines for a stronger comparison.
