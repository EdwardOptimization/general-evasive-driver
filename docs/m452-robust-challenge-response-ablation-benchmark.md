# M452 Robust Challenge Response Ablation Benchmark

## Purpose

M452 reruns the M450 response/history ablation diagnostic using the M451 robust
challenge configs. This is a generalization diagnostic only: no training, no
checkpoint promotion, and no actor input/output contract change.

Mainline actor remains:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

## Commands

Near-threshold robust challenge:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.benchmark \
  --env-config configs/m451_challenge_near_threshold_robust_zero_relvel.json \
  --episodes 128 \
  --seed 9900 \
  --policies heuristic \
  --checkpoint-policy m399_base=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --checkpoint-policy m399_reset=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt@reset_recurrent_state \
  --checkpoint-policy m399_zero_current=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt@zero_current_response \
  --checkpoint-policy m399_zero_all=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt@zero_all_response \
  --checkpoint-policy m399_noact=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt@zero_action_history \
  --device cpu \
  --run-dir runs/m452_near_robust_ablation_seed9900
```

Late high-energy robust challenge:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.benchmark \
  --env-config configs/m451_challenge_late_high_energy_robust_zero_relvel.json \
  --episodes 128 \
  --seed 9900 \
  --policies heuristic \
  --checkpoint-policy m399_base=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --checkpoint-policy m399_reset=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt@reset_recurrent_state \
  --checkpoint-policy m399_zero_current=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt@zero_current_response \
  --checkpoint-policy m399_zero_all=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt@zero_all_response \
  --checkpoint-policy m399_noact=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt@zero_action_history \
  --device cpu \
  --run-dir runs/m452_late_robust_ablation_seed9900
```

Policy-difference mining was then run on each episodes CSV with `m399_base` as
baseline and only the four ablation policies as candidates.

## Aggregate Results

### Near Robust

| policy | success | collision | mean margin | min margin | return |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | `0.351562` | `0.632812` | `0.315509` | `-0.326149` | `50.406799` |
| m399_base | `0.906250` | `0.085938` | `2.149732` | `-0.191466` | `76.764253` |
| m399_noact | `0.906250` | `0.085938` | `2.149458` | `-0.190874` | `76.781216` |
| m399_reset | `0.882812` | `0.093750` | `2.119200` | `-0.078188` | `74.166128` |
| m399_zero_all | `0.859375` | `0.093750` | `2.148677` | `-0.110892` | `73.260145` |
| m399_zero_current | `0.859375` | `0.093750` | `2.148677` | `-0.110892` | `73.260145` |

Near deltas versus `m399_base`:

| policy | success delta | collision delta | margin delta | return delta |
| --- | ---: | ---: | ---: | ---: |
| m399_noact | `0.000000` | `0.000000` | `-0.000273` | `0.016963` |
| m399_reset | `-0.023438` | `0.007812` | `-0.030532` | `-2.598125` |
| m399_zero_all | `-0.046875` | `0.007812` | `-0.001054` | `-3.504108` |
| m399_zero_current | `-0.046875` | `0.007812` | `-0.001054` | `-3.504108` |

### Late Robust

| policy | success | collision | mean margin | min margin | return |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | `0.312500` | `0.671875` | `0.252585` | `-0.304330` | `47.641051` |
| m399_base | `0.859375` | `0.140625` | `1.864845` | `-0.168443` | `76.240945` |
| m399_noact | `0.867188` | `0.132812` | `1.860293` | `-0.166392` | `76.920184` |
| m399_reset | `0.851562` | `0.148438` | `1.860257` | `-0.202351` | `74.143938` |
| m399_zero_all | `0.851562` | `0.148438` | `1.869915` | `-0.181439` | `74.178656` |
| m399_zero_current | `0.851562` | `0.148438` | `1.869915` | `-0.181439` | `74.178656` |

Late deltas versus `m399_base`:

| policy | success delta | collision delta | margin delta | return delta |
| --- | ---: | ---: | ---: | ---: |
| m399_noact | `0.007812` | `-0.007812` | `-0.004552` | `0.679239` |
| m399_reset | `-0.007812` | `0.007812` | `-0.004588` | `-2.097007` |
| m399_zero_all | `-0.007812` | `0.007812` | `0.005070` | `-2.062289` |
| m399_zero_current | `-0.007812` | `0.007812` | `0.005070` | `-2.062289` |

## Flip Diagnostics

Near robust has a small but real response-ablation signal:

- `m399_zero_current` and `m399_zero_all`: `6` base-success to ablation-fail
  flips, `0` ablation rescues;
- `m399_reset`: `3` base-success to ablation-fail flips;
- `m399_noact`: `0` outcome flips.

Most near zero-response flips are road-boundary failures rather than obstacle
collisions: five have positive clearance margin and lateral peak above the
track-width boundary; one seed (`10024`) is a low-mu near-boundary collision
where margin crosses from `0.047326` to about `-0.003616`.

Late robust is weaker:

- `m399_reset`, `m399_zero_current`, and `m399_zero_all` each have one
  base-success to ablation-fail flip at seed `9902`;
- `m399_noact` has one ablation rescue at seed `9942`;
- the strongest flip rows are near-boundary collision sign changes rather than
  broad success-rate separation.

## Policy Difference Mining

Near mining output:

- run dir: `runs/m452_near_ablation_policy_difference_mining`
- rows compared: `512`
- accepted rows: `319`
- compact rows: `64`
- accepted divergence counts: `success_flip=15`, `collision_flip=3`,
  `margin_sign_flip=3`, `near_boundary_margin_delta=44`,
  `large_margin_delta=175`, `return_delta=246`
- compact corpus is source-diverse: max policy dominance `0.359375`, max label
  dominance `0.375`, and low/medium/high mu buckets are represented.

Late mining output:

- run dir: `runs/m452_late_ablation_policy_difference_mining`
- rows compared: `512`
- accepted rows: `364`
- compact rows: `64`
- accepted divergence counts: `success_flip=4`, `collision_flip=4`,
  `margin_sign_flip=4`, `near_boundary_margin_delta=79`,
  `large_margin_delta=187`, `return_delta=256`
- compact corpus is also source-diverse by policy, obstacle label, and mu
  bucket.

## Decision

M452 passes as a runnable diagnostic gate, but it is not strong self-ID
evidence. The robust configs expose weak current-response sensitivity, most
clearly on the near robust distribution. They do not show strong recurrent
history necessity:

- reset-hidden degradation is small;
- zero-action-history degradation is absent or beneficial;
- zero-current and zero-all are identical here, so the observed signal is best
  interpreted as explicit current-response dependence, not proof that recurrent
  self-identification is necessary.

The robust challenge configs are useful as a seed source and diagnostic
scaffold, but not yet sufficient as a promotion-grade self-ID gate.

Next blocker:

```text
m453-response-critical-ablation-corpus-design
```

M453 should turn the M452 flip and large-delta evidence into a preregistered
response-critical corpus expansion plan. The key requirement is to separate:

- current-response dependence;
- recurrent-hidden dependence;
- action-history dependence;
- road-boundary failures versus true obstacle-collision margin failures.
