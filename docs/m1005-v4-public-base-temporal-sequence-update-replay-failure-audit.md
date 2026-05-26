# M1005 V4 Public Base Temporal Sequence Update Replay Failure Audit

## Purpose

M1005 audits why the M1002 exact temporal sequence objective candidates failed
the M1004 public replay preflight.

This milestone does not run training, PPO, private holdout, full public replay,
or promotion.

## Inputs

```text
runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/summary.json
runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/exact_contract_summary.csv
runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/candidate_preflight_summary.csv
runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/candidate_preflight/*/boundary_replay_rows.csv
```

## What Passed

The failure is not a stale checkpoint or actor-contract artifact.

```text
exact_contract_pass_count: 5 / 5
actor_inputs_changed: false
non_actor_parameter_changed: false
training_started: false
ppo_used: false
promoted: false
```

The exact temporal objective also behaved as designed: higher alphas improve
weighted total loss, temporal preference loss, and logp gap while staying inside
the M1002 exact action-drift trust region through alpha `0.2`.

## What Failed

All candidates fail M267/M264 success-drop retention:

| alpha | base drops | candidate drops | lost drops |
| --- | ---: | ---: | ---: |
| 0.20 | 17 | 6 | 11 |
| 0.10 | 17 | 11 | 6 |
| 0.05 | 17 | 13 | 4 |
| 0.02 | 17 | 15 | 2 |
| 0.01 | 17 | 15 | 2 |

Normal success is retained for every alpha:

```text
normal_success_delta: 0.0 for all alphas
```

Normal margin also improves for every alpha. The problem is the wrong-history
branch, not normal-branch safety.

## Smallest-Alpha Failure Rows

Alpha `0.01` loses rows `6` and `15`.

```text
row 6
  base normal/wrong margins:       0.011315 / -0.000117
  alpha 0.01 normal/wrong margins: 0.011511 /  0.000033

row 15
  base normal/wrong margins:       0.006403 / -0.000025
  alpha 0.01 normal/wrong margins: 0.006630 /  0.000171
```

Both rows are already extremely close to the terminal-margin boundary under
wrong history. A very small actor_mean update lifts the wrong-history rollout
above zero while also slightly improving normal margin.

## Failure Classification

```text
failure_type: proof_washout
subtype: wrong_history_branch_lift
scope: localized near-boundary M267/M264 rows, monotonic with alpha
```

Rejected alternatives:

```text
contract_violation: no
training_instability: no
metric_artifact: not primary
behavior_regression: not evaluated because preflight blocks behavior gate
scenario_sampling_failure: no
```

This is an objective-design issue. The M999/M1002 exact objective improves the
normal temporal sequence and separates normal hidden from disrupted temporal
hidden on that sequence, but it does not explicitly preserve public
wrong-history proof rows. Because the update is actor_mean-only, a globally
safer action bias can make the rejected/wrong-history branch safer too.

## Supported Claims

- M1002 exact temporal candidates are real exact-objective candidates.
- Actor_mean-only temporal objective movement is strong enough to change
  closed-loop public proof rows.
- The first public proof failure is not broad normal success regression.
- M267/M264 rows `6` and `15` are the active proof constraints for the smallest
  temporal update.

## Unsupported Claims

- M1002 candidates are not public-replay-valid.
- M1002 candidates are not promotable.
- M1002 candidates do not justify PPO continuation.
- M1002 does not prove cross-fault wrong-history self-identification.

## Decision

```text
temporal_sequence_replay_failure_audit_route_to_branch_preserving_temporal_repair_design
```

The next objective must keep the useful temporal sequence signal, but add an
explicit branch-preserving public-proof term before another actor update:

```text
1. normal temporal sequence retention from M997 remains a positive target;
2. disrupted temporal histories remain contrast-only, not degraded-action
   imitation targets;
3. M267/M264 wrong-history proof rows, especially rows 6 and 15, become
   lexicographic retention constraints;
4. candidate selection still starts with exact objective gates, then M267/M264
   preflight before full replay;
5. no PPO or promotion before that repaired objective has a preflight-passing
   candidate.
```

Next:

```text
m1006-v4-public-base-branch-preserving-temporal-repair-design
```
