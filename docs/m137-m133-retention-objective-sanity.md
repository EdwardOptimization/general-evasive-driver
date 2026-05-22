# M137 M133 Retention Objective Sanity

M137 tests whether objective-only training on the M136 M133 proof-surface
retention corpus can preserve the strict rows that M134/M135 PPO shrank.

## Baseline Retention Loss

Run directory: `runs/m137_baseline_m136_retention_eval_seed0`.

| Policy | M136 loss mean |
| --- | ---: |
| M132 s60 | 0.106838 |
| M134 step4096 | 0.106971 |
| M135 s2048 a1 | 0.106889 |

M134/M135 are slightly worse than M132 on the explicit M136 retention corpus,
which supports using M136 as the next objective target.

## Objective Candidates

All candidates start from
`runs/m132_margin_retention_s60_anchor20_seed9841/optimized_checkpoint.pt` and
train only actor-coupling parameters with frozen `log_std`.

| Candidate | Steps | LR | Anchor coef | M136 loss after | Improvement |
| --- | ---: | ---: | ---: | ---: | ---: |
| s20 a20 | 20 | 5e-5 | 20 | 0.104333 | 0.002505 |
| s40 a20 | 40 | 5e-5 | 20 | 0.102648 | 0.004191 |
| s40 a50 | 40 | 2e-5 | 50 | 0.105241 | 0.001597 |

M128 fixed outcome loss also improves:

| Candidate | M128 loss mean | Delta vs M132 |
| --- | ---: | ---: |
| M132 s60 | 0.252310 | 0.000000 |
| s20 a20 | 0.247032 | -0.005278 |
| s40 a20 | 0.243741 | -0.008570 |
| s40 a50 | 0.248916 | -0.003394 |

This means the objective update is not merely overfitting M136 while damaging
the older M128 fixed corpus.

## Behavior Gate

Run directory: `runs/m137_behavior_gate_seed9503`.

| Policy | Success | Termination | Clearance mean |
| --- | ---: | ---: | ---: |
| M132 s60 | 0.8625 | 0.1375 | 1.841558 |
| s20 a20 | 0.8625 | 0.1375 | 1.840780 |
| s40 a20 | 0.8625 | 0.1375 | 1.840605 |
| s40 a50 | 0.8625 | 0.1375 | 1.840974 |

For the best fixed-loss candidate, `s40 a20`, ablations remain consistent with
M133:

| Ablation | Success |
| --- | ---: |
| normal | 0.8625 |
| reset | 0.8500 |
| zero-current | 0.8000 |
| zero-all | 0.8000 |
| no-action | 0.8625 |

Behavior retention passes, and the zero-response gap remains visible.

## Strict Proof-Surface Gate

All strict runs use the M133 zero-relvel snapshot-bank relocation settings.

| Policy | Miner seed | Accepted rows | Success-drop pairs | Selected pairs | Selected seeds | Snippets | Max snippet gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M133 M132 s60 | 9900 | 18 | 5 | 10 | 8 | 17 | 0.029413 |
| M133 M132 s60 | 9920 | 15 | 4 | 9 | 8 | 14 | 0.029413 |
| s20 a20 | 9900 | 13 | 11 | 6 | 5 | 13 | 0.026464 |
| s20 a20 | 9920 | 11 | 9 | 5 | 4 | 11 | 0.026464 |
| s40 a20 | 9900 | 13 | 6 | 7 | 6 | 12 | 0.026136 |
| s40 a20 | 9920 | 11 | 6 | 6 | 5 | 10 | 0.026136 |
| s40 a50 | 9900 | 15 | 8 | 7 | 5 | 15 | 0.027811 |
| s40 a50 | 9920 | 11 | 5 | 5 | 4 | 11 | 0.027811 |

The fixed objective improves M136 and M128 losses, but all three candidates
shrink the strict rollout proof surface well below M133. The strongest fixed
loss candidate, `s40 a20`, reaches only `7` selected pairs/`6` seeds and `6`
pairs/`5` seeds.

## Decision

Reject M137 as a proof-surface repair.

This is a clear loss-misalignment result:

- fixed M136 retention loss improves;
- fixed M128 outcome loss also improves;
- behavior retention passes;
- strict rollout-level selected diversity collapses.

The next step should not be another direct logprob objective. It should audit
which M133 keys are lost and how fixed loss improvement changes rollout margin
gaps, then design a rollout-aware retention guard.

## Next Step

M138 should run a key-level retention-loss versus rollout-margin misalignment
audit before any further objective or PPO continuation.
