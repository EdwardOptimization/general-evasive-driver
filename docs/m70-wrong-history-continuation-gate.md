# M70 Wrong-History Continuation Gate

M69 found a few matched-action candidates where wrong recurrent history changed
the first action. M70 tests whether those first-action differences matter for
continuation outcomes.

The pass criterion is outcome-level:

```text
wrong history must reduce success or clearance margin,
not merely change the first action.
```

## Harness Update

`hidden_swap_gate` now records clearance margin in continuation replay outputs:

```text
min_clearance_margin
obstacle_collision_radius
min_obstacle_clearance
```

The summary CSV now includes:

```text
min_clearance_margin_mean
min_clearance_margin_min
min_obstacle_clearance_mean
```

This prevents M70 from relying on obstacle clearance as a proxy when the margin
is available.

## Candidate Seeds

Tracked candidates:

- `experiments/m70_brake_wrong_history_candidate_seeds.csv`
- `experiments/m70_friction_wrong_history_candidate_seeds.csv`
- `experiments/m70_wrong_history_candidate_seeds.csv`

Brake candidates:

```text
7019
7059
7002
```

Friction candidate:

```text
6905
```

## Commands

Weak-brake continuation:

```text
conda run -n autodrift python -m autodrift.hidden_swap_gate \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --seed-csv experiments/m70_brake_wrong_history_candidate_seeds.csv \
  --seed 7201 \
  --device cpu \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.85,1.15 \
  --nominal-randomization brake_scale_range=1.20,1.40 \
  --perturbed-randomization brake_scale_range=0.50,0.60 \
  --max-observation-distance 10.0 \
  --max-continuation-steps 0 \
  --run-dir runs/m70_wrong_history_continuation_brake_candidates_margin_seed7201
```

Friction continuation:

```text
conda run -n autodrift python -m autodrift.hidden_swap_gate \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --seed-csv experiments/m70_friction_wrong_history_candidate_seeds.csv \
  --seed 7202 \
  --device cpu \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.25,0.35 \
  --max-observation-distance 10.0 \
  --max-continuation-steps 0 \
  --run-dir runs/m70_wrong_history_continuation_friction_candidates_margin_seed7202
```

## Result

Weak-brake normal versus hidden-swap deltas:

| Seed | Source | Success Delta | Margin Delta | Return Delta | First Action Dist | Traj. Action Dist |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 7019 | nominal | 0 | -0.001416 | 0.042973 | 0.069026 | 0.014438 |
| 7019 | perturbed | 0 | 0.000239 | -0.085990 | 0.068225 | 0.017976 |
| 7059 | nominal | 0 | -0.000041 | 0.049012 | 0.052808 | 0.010785 |
| 7059 | perturbed | 0 | 0.000090 | -0.083111 | 0.052911 | 0.011748 |
| 7002 | nominal | 0 | 0.000108 | 0.044282 | 0.050926 | 0.013462 |
| 7002 | perturbed | 0 | -0.000259 | -0.110224 | 0.052539 | 0.018947 |

Weak-brake aggregate:

```text
success delta: 0 for every continuation
mean margin delta: -0.000213 m
worst margin delta: -0.001416 m
```

Friction normal versus hidden-swap deltas:

| Seed | Source | Success Delta | Margin Delta | Return Delta | First Action Dist | Traj. Action Dist |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 6905 | nominal | 0 | 0.001717 | -0.004772 | 0.051810 | 0.001844 |
| 6905 | perturbed | 0 | -0.000378 | 0.014160 | 0.046681 | 0.001774 |

Friction aggregate:

```text
success delta: 0 for every continuation
mean margin delta: 0.000670 m
worst margin delta: -0.000378 m
```

## Interpretation

M70 is negative.

The wrong-history candidate seeds do change first action enough to pass the M69
threshold, but the changes rapidly collapse during closed-loop continuation:

- every normal and hidden-swap replay succeeds;
- terminal reason remains `obstacle_completed`;
- margin differences are millimeter-scale;
- trajectory action distances after the first step are small.

This is not enough for a self-identification training target. The policy can
absorb these wrong-history perturbations without meaningful outcome damage.

## Next Step

Stop mining only from passive near-matched snapshots in the current M67-E teacher.

The next milestone should construct a stronger outcome-sensitive scenario:

```text
same visible emergency geometry
larger hidden dynamics contrast
closer obstacle timing
lower clearance margin
wrong history or wrong capability belief causes collision or margin loss
```

The likely implementation is a paired scenario constructor or gate that samples
near-boundary weak-brake / low-friction cases and rejects candidates unless
normal-history margin exceeds wrong-history margin by a preregistered threshold.
