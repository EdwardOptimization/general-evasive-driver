# M135 PPO Step And Anchor Sensitivity Gate

M135 tests whether M134's proof-surface regression can be fixed by smaller PPO
steps or stronger action anchoring. The grid was fixed before looking at strict
proof-surface results.

## Candidate Grid

All candidates start from
`runs/m132_margin_retention_s60_anchor20_seed9841/optimized_checkpoint.pt`, use
the M121 zero-relvel human-view observation contract, freeze `log_std`, and use
the M128 outcome snippets.

| Candidate | Config | Steps | Anchor coef | Anchor mode |
| --- | --- | ---: | ---: | --- |
| s2048 a1 | `configs/ppo_m135_step2048_anchor1_neg.json` | 2048 | 1.0 | negative-advantage only |
| s2048 a20 | `configs/ppo_m135_step2048_anchor20_all.json` | 2048 | 20.0 | all states |
| s4096 a20 | `configs/ppo_m135_step4096_anchor20_all.json` | 4096 | 20.0 | all states |

M134 step4096 serves as the existing `4096 + anchor1 negative-only` control.

## PPO Smoke

| Candidate | Run dir | Eval return | Eval termination |
| --- | --- | ---: | ---: |
| s2048 a1 | `runs/ppo_m135_step2048_anchor1_neg_seed5235` | 74.785273 | 0.0000 |
| s2048 a20 | `runs/ppo_m135_step2048_anchor20_all_seed5236` | 71.468562 | 0.0000 |
| s4096 a20 | `runs/ppo_m135_step4096_anchor20_all_seed5237` | 60.326300 | 0.2000 |

Built-in PPO eval remains a smoke signal only.

## Behavior Gate

Run directory: `runs/m135_behavior_gate_seed9503`.

| Policy | Success | Termination | Clearance mean | Reset success | Zero-response success | No-action success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M132 s60 | 0.8625 | 0.1375 | 1.841558 | - | - | - |
| M134 step4096 | 0.8625 | 0.1375 | 1.842102 | - | - | - |
| M135 s2048 a1 | 0.8625 | 0.1375 | 1.841379 | 0.8500 | 0.8000 | 0.8625 |
| M135 s2048 a20 | 0.8625 | 0.1375 | 1.841647 | 0.8500 | 0.8000 | 0.8625 |
| M135 s4096 a20 | 0.8625 | 0.1375 | 1.841979 | 0.8500 | 0.8000 | 0.8625 |

All candidates retain behavior, retain the zero-response degradation, and keep
the no-action limitation.

## Fixed-Batch Outcome Loss

Run directory: `runs/m135_outcome_intervention_eval_seed0`.

| Policy | M128 loss mean | Delta vs M132 |
| --- | ---: | ---: |
| M132 s60 | 0.252310 | 0.000000 |
| M134 step4096 | 0.251846 | -0.000464 |
| M134 final | 0.251741 | -0.000569 |
| M135 s2048 a1 | 0.252178 | -0.000132 |
| M135 s2048 a20 | 0.252404 | +0.000094 |
| M135 s4096 a20 | 0.252389 | +0.000079 |

The smaller anchor1 run improves the fixed loss only slightly. Strong all-state
anchor protects behavior but worsens the fixed M128 loss.

## Strict Proof-Surface Gate

All strict runs use the M133 zero-relvel snapshot-bank relocation settings.

| Policy | Miner seed | Accepted rows | Success-drop pairs | Selected pairs | Selected seeds | Snippets | Max snippet gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M133 M132 s60 | 9900 | 18 | 5 | 10 | 8 | 17 | 0.029413 |
| M133 M132 s60 | 9920 | 15 | 4 | 9 | 8 | 14 | 0.029413 |
| M134 step4096 | 9900 | 17 | 7 | 9 | 6 | 17 | 0.034492 |
| M134 step4096 | 9920 | 17 | 6 | 9 | 7 | 17 | 0.034492 |
| M135 s2048 a1 | 9900 | 17 | 6 | 9 | 7 | 16 | 0.032692 |
| M135 s2048 a1 | 9920 | 17 | 5 | 9 | 8 | 16 | 0.032692 |
| M135 s2048 a20 | 9900 | 17 | 5 | 8 | 6 | 16 | 0.032634 |
| M135 s2048 a20 | 9920 | 17 | 3 | 8 | 7 | 16 | 0.032634 |
| M135 s4096 a20 | 9900 | 17 | 7 | 9 | 6 | 17 | 0.034544 |
| M135 s4096 a20 | 9920 | 17 | 6 | 9 | 7 | 17 | 0.034544 |

The best candidate is `s2048 a1`: it reaches `9` pairs/`7` seeds on seed9900
and `9` pairs/`8` seeds on seed9920. That is an improvement over M134
step4096, but it still fails the M133 seed9900 standard of `10` pairs/`8`
seeds.

All accepted snippet exports remain perturbed-source only.

## Decision

Reject PPO sensitivity branch.

M135 shows that smaller PPO steps reduce the proof-surface damage, but do not
solve it. Strong all-state anchoring does not help: it worsens fixed M128 loss
and still fails selected-seed diversity. Further PPO should not proceed until
the M133 strict proof-surface rows are represented directly as a retention
corpus or objective guard.

## Next Step

M136 should build or audit an explicit M133 proof-surface retention corpus. The
next PPO/objective recipe should be gated against the exact strict selected
rows that M134/M135 shrink, instead of relying only on generic M128 outcome
snippets and behavior anchors.
