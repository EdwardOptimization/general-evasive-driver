# M132 Rollout Margin Retention Repair

M131 showed that M129 improved fixed snippet logprob loss while shrinking fresh
rollout margin gaps. M132 tests a conservative repair: smaller updates from M124
with a stronger action anchor.

This is a repair-candidate milestone, not PPO admission.

## Objective Candidates

Both candidates start from:

```text
runs/m124_calib_s120_lr5e5_anchor10_seed9821/optimized_checkpoint.pt
```

and train on:

```text
runs/m128_combined_outcome_snippet_corpus/outcome_intervention_snippets.npz
```

| Candidate | Steps | Anchor coef | Seed | Before loss | After loss | Improvement | After anchor MSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| s40 anchor20 | 40 | 20 | 9840 | 0.281314 | 0.260002 | 0.021312 | 0.000289 |
| s60 anchor20 | 60 | 20 | 9841 | 0.281314 | 0.252310 | 0.029004 | 0.000341 |

These improvements are much smaller than M129's `0.102-0.110`, but the goal is
proof-surface retention, not fixed-corpus loss maximization.

## Strict Proof Surface

All strict miners use the M121 zero-relvel profile and the M127 thresholds.

| Policy | Miner seed | Accepted rows | Success-drop pairs | Selected pairs | Selected seeds | Snippets | Max snippet gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M129 | 9860 | 14 | 8 | 5 | 4 | 14 | 0.015155 |
| M129 | 9880 | 9 | 7 | 3 | 3 | 9 | 0.015155 |
| s40 anchor20 | 9860 | 20 | 8 | 6 | 4 | 20 | 0.031289 |
| s60 anchor20 | 9860 | 21 | 9 | 7 | 5 | 21 | 0.032615 |
| s60 anchor20 | 9880 | 13 | 10 | 5 | 4 | 13 | 0.029413 |

The s60/anchor20 candidate is the better repair. It recovers selected-pair
diversity and margin-gap magnitude relative to M129, especially on miner seed
`9860`.

All exported s60 snippets are still perturbed-source:

```text
seed 9860: {'perturbed': 21}
seed 9880: {'perturbed': 13}
```

## Behavior Gate

Run:

```text
runs/m132_margin_retention_s60_behavior_gate_seed9502
```

| Policy | Success | Termination | Return mean | Clearance mean | Clearance min |
| --- | ---: | ---: | ---: | ---: | ---: |
| M124 9821 | 0.8625 | 0.1375 | 65.673907 | 1.849902 | -0.125811 |
| s60 anchor20 | 0.8625 | 0.1375 | 65.712684 | 1.848169 | -0.144814 |
| s60 reset | 0.8500 | 0.1500 | 63.845770 | 1.847116 | -0.168903 |
| s60 zero-current | 0.8000 | 0.2000 | 60.768676 | 1.863072 | -0.145811 |
| s60 zero-all | 0.8000 | 0.2000 | 60.768676 | 1.863072 | -0.145811 |
| s60 no-action | 0.8625 | 0.1375 | 65.250944 | 1.852488 | -0.133690 |

Behavior retention passes. Zero-response degradation remains. No-action history
is still neutral.

## Decision

Admit the s60/anchor20 repair candidate to formal repeat, not PPO.

What improved versus M129:

- proof-surface selected pairs recover from `5/3` to `7/5` across the tested
  miner seeds;
- max snippet gap recovers from `0.015155` to about `0.029-0.033`;
- behavior retention remains at M124 success;
- anchor drift is much smaller than M129.

What still blocks PPO:

- seed `9880` is improved but still only `5` selected pairs and `4` seeds;
- no-action history remains neutral;
- source-side coverage is still perturbed-only;
- this has not been repeated on fresh behavior and miner seeds beyond the repair
  selection tests.

Next step: M133 should run a formal repeat gate for the s60/anchor20 candidate
before any PPO continuation.
