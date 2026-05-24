# M582 BC5660 Recurrent Ablation Fresh Route Eval

## Purpose

M582 runs the first recurrent-dependence diagnostic for the scaled BC branch.
The checkpoint, route seeds, ablations, and thresholds were pre-registered in
M581 before any ablation result was observed.

This milestone is diagnostic only:

```text
no training
no PPO
no behavior cloning
no checkpoint promotion
```

## Command

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --policies checkpoint \
  --checkpoint-policy bc5660_normal=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --checkpoint-policy bc5660_reset=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy bc5660_zero_current=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt@zero_current_response \
  --checkpoint-policy bc5660_zero_action=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt@zero_action_history \
  --checkpoint-policy bc5660_zero_all=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt@zero_all_response \
  --episodes 256 \
  --seed 23560 \
  --device cpu \
  --env-config configs/ppo_m541_matched_l3_variance_4096.json \
  --run-dir runs/m582_bc5660_recurrent_ablation_fresh_route_eval
```

The first run exposed an infrastructure issue: `autodrift.benchmark` required
`--checkpoint` even when all checkpoint policies were supplied through named
`--checkpoint-policy` entries. This was fixed separately in commit `c0778b6`
with focused tests, then the exact M582 command above was rerun.

## Artifacts

```text
runs/m582_bc5660_recurrent_ablation_fresh_route_eval/manifest.json
runs/m582_bc5660_recurrent_ablation_fresh_route_eval/episodes.csv
runs/m582_bc5660_recurrent_ablation_fresh_route_eval/policy_summary.csv
```

`episodes.csv` has `1281` rows: one header plus `5 * 256` evaluated episodes.

## Results

| policy | success | collision | return | mean margin | min margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| bc5660_normal | 0.691406 | 0.308594 | 65.244561 | 1.068165 | -0.279645 |
| bc5660_reset | 0.683594 | 0.316406 | 64.836896 | 1.050572 | -0.281763 |
| bc5660_zero_action | 0.679688 | 0.320312 | 64.587176 | 1.015206 | -0.246172 |
| bc5660_zero_all | 0.664062 | 0.335938 | 63.536030 | 0.923356 | -0.274557 |
| bc5660_zero_current | 0.664062 | 0.335938 | 63.536030 | 0.923356 | -0.274557 |

Delta against `bc5660_normal`:

| ablation | success drop | margin drop | collision increase | return delta | label |
| --- | ---: | ---: | ---: | ---: | --- |
| reset_recurrent_state | 0.007812 | 0.017594 | 0.007812 | -0.407665 | weak |
| zero_action_history | 0.011719 | 0.052959 | 0.011719 | -0.657385 | meaningful |
| zero_all_response | 0.027344 | 0.144810 | 0.027344 | -1.708531 | strong |
| zero_current_response | 0.027344 | 0.144810 | 0.027344 | -1.708531 | strong |

M581 thresholds:

```text
meaningful:
  success_drop >= 0.02
  OR margin_drop >= 0.05
  OR collision_increase >= 0.02

strong:
  success_drop >= 0.05
  OR margin_drop >= 0.10
  OR collision_increase >= 0.05
```

## Interpretation

M582 is a positive deployable-response diagnostic, but not a complete
self-identification proof.

The strongest signal is `zero_current_response`: removing the current
ego/IMU-like response and actuator/command-response slots lowers success by
`0.027344`, increases collision by `0.027344`, and drops mean clearance margin
by `0.144810`. The margin drop crosses the pre-registered strong threshold.

`zero_action_history` crosses the meaningful threshold through clearance margin
drop (`0.052959`). This supports keeping previous physical commands in the
human-view contract because the policy does worse when it cannot relate recent
commands to vehicle response.

`reset_recurrent_state` is only weak on this same-distribution route block. That
means M582 does not prove that accumulated online hidden state is critical on
these seeds. A plausible reading is that BC5660 relies heavily on the current
response frame and some previous-command information, while longer hidden
belief still needs stronger diagnostics such as OOD ablation, delayed-history,
or wrong-history interventions.

`zero_current_response` and `zero_all_response` are numerically identical here.
For the one-frame L3 input, the severe control did not add measurable
degradation beyond removing the current response stream.

## Decision

```text
bc5660_fresh_route_response_ablation_positive_admit_m583_ood
```

M582 passes as a positive fresh-route response/action ablation diagnostic.
Promotion and PPO remain blocked because this is not a promotion gate and does
not yet establish accumulated hidden-state self-identification.

## Next

```text
M583: repeat the same recurrent-ablation diagnostic on moderate-OOD route seeds.
```
