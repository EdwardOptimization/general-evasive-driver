# M1117 V4 Public Base Materialized Objective Branch Synthesis

## Purpose

M1117 synthesizes the `materialized_objective_corpus_sanity` branch before any
new actor-update implementation.

This milestone is process-only. It does not train actor weights, run PPO, run
replay, run objective optimization, mine rows, promote a checkpoint, use private
holdout, or change actor inputs.

## Evidence Summary

M1107 produced the first valid materialized objective corpus for the current
public-gate base:

```text
rows: 68
physical_pairs: 14
targets: 3
success_drop_rows: 68
action_reconstruction_error_max: 0.0
objective_pass: true
seed_pass_count: 3
mean_val_combined_loss_improvement: 2.951631
mean_val_pairwise_accuracy_after: 0.944444
```

M1108 admitted only a guarded actor-update design, not a direct update or PPO.
M1109 specified a low-drift `actor_coupling` update with frozen `log_std`,
rollout action anchors, and snippet action anchors including rejected hidden
states.

M1110 ran three candidates. All improved exact M1107 loss while changing only
the allowed parameter surface:

```text
base exact M1107 loss: 0.679117
m1110_110900 exact loss: 0.674470
m1110_110901 exact loss: 0.674349
m1110_110902 exact loss: 0.674359
```

M1111 designed the full public gate for the best candidate. M1112 then rejected
that candidate: exact objective and contract gates passed, but expanded public
proof replay failed. Fresh/OOD and behavior gates still passed, so the failure
was not broad behavior collapse.

M1113 audited the replay artifacts and found a specific failure mode:

```text
lost_success_drop_events: 47
normal_lost_events: 0
wrong_history_safe_events: 47
```

M1114 designed a failed wrong-history retention export and forbade direct use
of short-family hidden states. M1115 implemented it:

```text
failed_event_count: 47
target_base_failed_events: 19
family_source_failed_events: 28
target_base_rejected_trajectory_anchor_rows: 707
combined_target_base_rejected_anchor_rows: 4664
short_family_rows_in_training_anchor: false
```

M1116 used M1115 to design a retention-aware actor-coupling probe. The planned
probe uses the M1107 exact objective, M1115 combined trajectory retention, and a
target-base-only trajectory-anchor gate before any replay.

## Supported Claims

This branch supports these claims:

```text
1. The M1107 materialized proof-current corpus is valid and learnable as an
   auxiliary objective.
2. A tightly scoped actor_coupling update can improve exact M1107 objective
   without changing forbidden parameter groups.
3. Exact objective improvement alone is insufficient; M1112 showed it can
   wash out wrong-history proof rows.
4. The M1112 failure is specifically wrong-history branches becoming safe,
   not normal-history success loss.
5. The failed wrong-history events can be deterministically exported and split
   into target-base rows and short-family diagnostic rows.
6. A target-base rejected-history trajectory anchor can be built in the
   current public-base hidden-state space without short-family leakage.
7. The next plausible repair direction is a retention-aware actor update, not
   more exact-objective-only training and not PPO.
```

## Falsified Or Unsupported Claims

This branch falsifies or does not support these claims:

```text
1. Exact M1107 objective improvement is enough to preserve closed-loop proof.
2. One-step action anchors and snippet anchors are sufficient to prevent
   wrong-history branches from becoming safe.
3. The M1110 candidate should be promoted or used as a base.
4. The branch proves driver improvement on scenario distributions.
5. The branch proves PPO readiness.
6. The branch proves private-holdout or paper-level generalization.
7. The branch proves level3 anticipatory self-identification.
```

The branch remains level2 evidence: replay-calibrated history sensitivity and
history-encoded reactive behavior are being protected. No result here proves
anticipatory self-identification.

## Failure Taxonomy Summary

The primary failure was:

```text
proof_washout:
  M1112 candidate passed exact objective and contract gates but failed old
  public replay, family-intersection replay, and source-diverse replay.

objective_overfit:
  M1110/M1112 showed that optimizing the materialized exact objective can
  improve the registered objective while damaging closed-loop proof rows.
```

The audit explicitly did not classify the failure as:

```text
behavior_regression:
  fresh/OOD and behavior gates passed.

contract_violation:
  changed tensors stayed within actor_mean. and response_context_fusion.0.

training_instability:
  optimizer artifacts were valid.

private_holdout_contamination:
  no private holdout was used.
```

M1115 converted the failure into infrastructure: a registry, target-base anchor,
family-source diagnostic split, and combined anchor.

## Public-Gate Overfit Risk

The branch uses public proof surfaces heavily. That is acceptable for proof
hardening, but it cannot be used as private generalization evidence.

Overfit controls added by the branch:

```text
exact objective sanity before update
allowed parameter-surface audit
expanded public proof replay after exact pass
M1113 failure-mode audit
target-base vs family-source split
short-family hidden-state exclusion
combined anchor plus target-base-only gate requirement
cadence synthesis before another narrow milestone
```

Remaining risks:

```text
1. M1118 may overfit the target-base failed rows while still failing
   family-intersection replay.
2. The M1115 anchor may be too strong and block exact objective movement.
3. The target-base-only trajectory gate may not predict closed-loop replay
   pass/fail perfectly.
4. The evidence is still public-proof-surface evidence, not private holdout.
```

Those risks must be handled by the M1118 pre-replay gates and then by explicit
first replay, source-diverse replay, family-intersection replay, and behavior
gates. Promotion remains out of scope.

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Closed branch:

```text
materialized_objective_corpus_sanity
```

Opened branch:

```text
failed_wrong_history_retention_repair
```

The next milestone should run the M1116-designed actor-update probe, not PPO and
not replay. The implementation scope is:

```text
M1118:
  run seeds 111800, 111801, 111802;
  restart each seed from the current public-gate base;
  train only actor_coupling with frozen log_std;
  use M1107 exact objective;
  use M1115 combined trajectory-action anchor;
  require exact, parameter-scope, action-anchor, snippet-anchor, combined
  trajectory-anchor, and target-base-only trajectory-anchor gates;
  do not run replay unless those gates pass in a later milestone;
  do not promote.
```

## Decision

```text
materialized_objective_branch_synthesis_open_failed_wrong_history_retention_repair
```

Next milestone:

```text
m1118-v4-public-base-failed-wrong-history-retention-actor-update-probe
```
