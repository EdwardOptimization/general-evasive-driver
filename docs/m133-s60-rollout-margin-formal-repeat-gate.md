# M133 S60 Rollout Margin Formal Repeat Gate

M133 formally repeats the M132 s60/anchor20 rollout-margin repair before any
PPO continuation. The purpose is not to claim a solved driver. The purpose is
to decide whether the repaired checkpoint is strong enough for a small guarded
PPO smoke continuation.

## Inputs

- Baseline: `runs/m124_calib_s120_lr5e5_anchor10_seed9821/optimized_checkpoint.pt`
- Candidate: `runs/m132_margin_retention_s60_anchor20_seed9841/optimized_checkpoint.pt`
- Behavior profile: `configs/m121_human_view_zero_obstacle_relvel.json`
- Strict miner profile: M127/M132 zero-relvel strict snapshot-bank relocation
  with 60 episodes, reveal step `20`, reveal distance `16`, bank distances
  `5,12`, stride `3`, relocation distances `10,11,12`, lateral offset `-1`,
  half widths `0.7..1.4`, max visible distance `0.75`, max response distance
  `0.35`, max context distance `0.05`, min margin gap `0.005`, max normal
  margin `0.20`, max continuation steps `40`, and accepted-only outcome export.

Exact command lines are preserved in the run manifests under `runs/m133_*`.

## Behavior Gate

Run directory:
`runs/m133_s60_formal_behavior_gate_seed9503`.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.benchmark \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --episodes 80 --seed 9503 --policies heuristic \
  --checkpoint-policy m124_9821=runs/m124_calib_s120_lr5e5_anchor10_seed9821/optimized_checkpoint.pt \
  --checkpoint-policy m132_s60=runs/m132_margin_retention_s60_anchor20_seed9841/optimized_checkpoint.pt \
  --checkpoint-policy m132_s60_reset=runs/m132_margin_retention_s60_anchor20_seed9841/optimized_checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m132_s60_zero_current=runs/m132_margin_retention_s60_anchor20_seed9841/optimized_checkpoint.pt@zero_current_response \
  --checkpoint-policy m132_s60_zero_all=runs/m132_margin_retention_s60_anchor20_seed9841/optimized_checkpoint.pt@zero_all_response \
  --checkpoint-policy m132_s60_noact=runs/m132_margin_retention_s60_anchor20_seed9841/optimized_checkpoint.pt@zero_action_history \
  --device cpu --run-dir runs/m133_s60_formal_behavior_gate_seed9503
```

| Policy | Success | Termination | Return | Clearance mean | Clearance min |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | 0.2375 | 0.7625 | 38.301741 | 0.131637 | -0.309701 |
| M124 | 0.8625 | 0.1375 | 65.645004 | 1.843230 | -0.125811 |
| M132 s60 | 0.8625 | 0.1375 | 65.685395 | 1.841558 | -0.144814 |
| M132 s60 no-action | 0.8625 | 0.1375 | 65.225304 | 1.845835 | -0.133690 |
| M132 s60 reset | 0.8500 | 0.1500 | 63.794619 | 1.840155 | -0.168903 |
| M132 s60 zero-current | 0.8000 | 0.2000 | 60.724458 | 1.855923 | -0.145811 |
| M132 s60 zero-all | 0.8000 | 0.2000 | 60.724458 | 1.855923 | -0.145811 |

Behavior retention passes: M132 s60 matches M124 success on the fresh behavior
seed. The zero-current and zero-all response ablations again drop to `0.8000`,
so the response-dependence signal remains visible. No-action history remains
neutral, which must remain a limitation rather than a proof claim.

## Strict Proof-Surface Gate

| Run | Accepted outcome-sensitive pairs | Success-drop pairs | Selected physical pairs | Selected seeds | Snippets | Max snippet gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| s60 seed 9900 | 18 | 5 | 10 | 8 | 17 | 0.029413 |
| s60 seed 9920 | 15 | 4 | 9 | 8 | 14 | 0.029413 |
| M62 control seed 9900 | 0 | 2 | 0 | 0 | 0 | 0.000000 |
| M62 control seed 9920 | 0 | 1 | 0 | 0 | 0 | 0.000000 |

Strict s60 miners exceed the immediate diversity threshold on two fresh seeds:
`10` physical pairs/`8` seeds and `9` physical pairs/`8` seeds. M62 controls
still export zero accepted snippets under the same strict profile.

## Source Coverage

The accepted snippet exports are still perturbed-source only:

| Run | Snippets | Source condition | Seeds |
| --- | ---: | --- | --- |
| s60 seed 9900 | 17 | perturbed | 9906, 9913, 9939, 9942, 9944, 9954, 9957 |
| s60 seed 9920 | 14 | perturbed | 9939, 9942, 9944, 9954, 9957, 9977, 9978 |

This is useful for outcome-centric self-ID gates, but it is not yet balanced
across nominal and perturbed source sides.

## Decision

M133 admits guarded PPO readiness, not driver success.

The checkpoint may enter a small guarded PPO continuation because:

- fresh behavior retention matches M124/M132;
- zero-response degradation repeats;
- fresh strict proof-surface diversity repeats above the M130/M132 blocker;
- M62 controls remain clean with zero exported snippets.

The next step must be a guarded PPO smoke continuation from M132 s60 with strict
post-PPO retention gates. PPO is rejected if it washes out behavior retention,
zero-response degradation, or the M133 proof-surface diversity.

## Limitations

- No-action history remains neutral.
- Accepted outcome snippets are still perturbed-source only.
- M133 does not prove full closed-loop self-identification.
- It only justifies the next guarded PPO experiment.
