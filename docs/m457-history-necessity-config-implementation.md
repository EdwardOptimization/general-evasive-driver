# M457 History-Necessity Config Implementation

## Purpose

M456 concluded that the M451 robust challenge family is useful for boundary
mining but not strong recurrent-history evidence. M457 implements the first
Layer A task-family config:

```text
configs/m457_history_necessity_late_reveal_zero_relvel.json
```

This milestone validates sampling and a tiny benchmark only. It does not train,
promote, or claim self-identification.

## Config

The final M457 config keeps the P0 human-view/no-wheel actor contract:

- `history_length: 1`
- `action_history_mode: full`
- `obstacle_relative_velocity_mode: zero`
- road boundary points and obstacle geometry remain ego-frame context;
- no hidden params, labels, TTC, required clearance, reference trajectory, or
  feasibility answers enter the actor.

The task uses a late reveal:

```text
obstacle.distance_range: [12.0, 30.0]
obstacle.perception_reveal_distance: 14.0
friction_step.enabled: true
friction_step.step_range: [6, 34]
friction_step.mu_range: [0.18, 1.05]
```

The initial stricter draft used `[18.0, 42.0]`, reveal `20.0`, threshold score
`0.45`, and `min_time_after_friction_step: 0.35`. It failed reset stress with
`71/384` scenario sampling failures. M457 therefore relaxes the obstacle window
and removes the extra min-time filter. The accepted rows still occur after the
friction step in reset stress, with a minimum recorded
`obstacle_time_after_friction_step` of `0.061738`.

## Reset Stress

Command:

```bash
PYTHONPATH=src python - <<'PY'
# reset stress over seeds 9600-9727, 9900-10027, 10150-10277
PY
```

Artifacts:

```text
runs/m457_late_reveal_reset_stress/summary.json
runs/m457_late_reveal_reset_stress/reset_rows.csv
```

Results:

| seed base | resets | failures | hidden at reset | visible at reset | labels |
| --- | ---: | ---: | ---: | ---: | --- |
| `9600` | 128 | 0 | 96 | 32 | aes 21, drift 75, unavoidable 32 |
| `9900` | 128 | 0 | 102 | 26 | aes 24, drift 73, unavoidable 31 |
| `10150` | 128 | 0 | 96 | 32 | aes 25, drift 75, unavoidable 28 |
| total | 384 | 0 | 294 | 90 | aes 70, drift 223, unavoidable 91 |

The final config passes the M457 reset-stress requirement: no sampling failures
across the three seed windows, and the obstacle is hidden at reset for
`294/384` cases.

## Tiny Benchmark

Command family:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.evaluate \
  --episodes 16 \
  --seed 9900 \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json
```

Results:

| policy | ablation | return mean | termination rate | mean clearance | min clearance |
| --- | --- | ---: | ---: | ---: | ---: |
| heuristic | none | 47.289250 | 0.687500 | 0.156736 | -0.333213 |
| M399 | none | 69.913729 | 0.250000 | 1.851653 | -0.169692 |
| M399 | reset recurrent | 68.096874 | 0.250000 | 1.863199 | -0.221804 |
| M399 | zero current response | 68.242046 | 0.250000 | 1.890589 | -0.100821 |
| M399 | zero action history | 73.146945 | 0.187500 | 1.848054 | -0.141948 |

M399 is clearly stronger than the heuristic on this tiny smoke, and the task is
not trivially impossible or solved. However, the ablations do not show strong
history necessity at 16 episodes. This is expected for M457: it only establishes
a runnable Layer A config.

## Decision

M457 passes as an infrastructure/config milestone:

- final config committed under an M457 name;
- reset stress passes `384/384` with no sampling failures;
- obstacle reveal is not immediate for most reset rows;
- tiny benchmark completes;
- no checkpoint is promoted;
- no actor input/output contract changes.

The next step is not training. The next step is a larger M458 response/history
ablation benchmark on this config, followed by matched-current mining only if
the larger benchmark produces useful source-diverse differences.
