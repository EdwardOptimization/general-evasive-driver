# M1338 Paper-Route Materialized Source-History Objective Evaluator Design

## Summary

M1338 designs the exact no-update evaluator for the M1336 active materialized
source-history corpus.

Decision:

```text
materialized_source_history_objective_evaluator_design_admit_no_update_implementation
```

Do not train.

Do not run PPO.

Do not update actor weights.

The next milestone should implement one evaluator:

```text
m1339-paper-route-materialized-source-history-objective-evaluator-implementation
```

## Why A New Evaluator Is Needed

The existing M1285 evaluator is useful but not directly sufficient. It expects
the older M1277/M1280 artifact split:

```text
intervention_observations.csv
intervention_action_sequences.csv
history_frame_rows.csv
history_intervention_rows.csv
wrong_history_pair_rows.csv
```

The M1336 active corpus is broader and already carries preferred/rejected
first-action targets in `active_history_intervention_rows.csv`, but it does not
carry full obstacle/road current observations. Therefore M1339 should implement
a dedicated materialized evaluator rather than silently forcing M1336 into the
M1285 interface.

The new evaluator is a source-history diagnostic, not a closed-loop driver
benchmark. It can measure whether a checkpoint's recurrent hidden state maps
correct histories toward preferred source actions and wrong histories toward
rejected source actions under a controlled source-current projection.

## Input Artifacts

Required artifacts:

```text
runs/m1336_materialized_source_history_objective_corpus_export/active_source_pair_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_history_prefix_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_history_frame_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_history_intervention_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_wrong_history_pair_rows.csv
```

Default checkpoint for the implementation smoke:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

This is the current public-gate base recorded earlier in the project. M1339 may
accept a `--checkpoint` CLI argument, but the manifest should name the exact
checkpoint it evaluates.

## Required Joins

M1339 should build these indexes:

```text
source_pair_by_pair_id
prefix_by_history_id
frames_by_history_id
history_intervention_by_history_intervention_id
wrong_history_pair_by_history_intervention_id
```

For every active `history_intervention_id`, require:

```text
correct_history_id exists in frames_by_history_id
wrong_history_id exists in frames_by_history_id
same_pair_swap == true
opposite_condition_swap == true
same_source_identity_swap == true
source_identity matches source pair metadata
preferred/rejected actions are finite
```

Any missing join is a contract failure, not a row to skip silently.

## Actor Observation Projection

History frames use the same first-12 human-view response fields already used in
the source-history policy gate:

```text
vx
vy
yaw_rate
ax
ay
steer_state
steer_rate
drive_state
brake_state
prev_cmd_steer
prev_cmd_throttle
prev_cmd_brake
```

Projection into the 72-value P0 actor frame:

```text
indices 0-11: normalized response/action-history fields
indices 12-71: zero context for this diagnostic
```

For action scoring, use a same-current source observation:

```text
o_source = project(final frame of correct_history_id, zero context)
```

Then score both hidden states against the same `o_source`:

```text
h_c = replay(correct history frames)
h_w = replay(wrong history frames)
```

This keeps the current observation fixed while changing only recurrent
command-response history. It also means the metric remains diagnostic-only:
zero scene context is not a deployable obstacle-avoidance observation, and the
current response frame can still substitute for part of the history.

## Action Targets

Read preferred and rejected source actions directly from
`active_history_intervention_rows.csv`:

```text
a_p = [preferred_steer, preferred_throttle, preferred_brake]
a_r = [rejected_steer, rejected_throttle, rejected_brake]
```

No fault label, source family, margin bucket, candidate id, success flag, or
hidden parameter may enter actor observations. Those fields are allowed only for
row grouping, reporting, and diagnostics.

## Objective Definition

For each active row:

```text
logp_cp = log pi(a_p | o_source, h_c)
logp_cr = log pi(a_r | o_source, h_c)
logp_wp = log pi(a_p | o_source, h_w)
logp_wr = log pi(a_r | o_source, h_w)
```

Correct-history preference:

```text
correct_preference_margin = logp_cp - logp_cr
L_correct = softplus(logp_cr - logp_cp + 0.05)
```

Wrong-history preference:

```text
wrong_history_preference_margin = logp_wr - logp_wp
L_wrong = softplus(logp_wp - logp_wr + 0.05)
```

Combined exact objective:

```text
L_materialized_source_history =
  mean(L_correct + L_wrong)
```

M1339 should not introduce row weights. The first evaluator should measure the
unweighted full active corpus exactly. Weighting or trainable-scope choices
belong to later design milestones.

## Action-Distance Diagnostics

Also record:

```text
mean_correct = policy mean under (o_source, h_c)
mean_wrong = policy mean under (o_source, h_w)
history_action_l2 = ||mean_correct - mean_wrong||_2
correct_distance_to_preferred = ||mean_correct - a_p||_2
correct_distance_to_rejected = ||mean_correct - a_r||_2
wrong_distance_to_preferred = ||mean_wrong - a_p||_2
wrong_distance_to_rejected = ||mean_wrong - a_r||_2
correct_closer_to_preferred
wrong_closer_to_rejected
```

These diagnostics separate three failure modes:

```text
history has no action effect;
history changes action but in the wrong direction;
log-probability improves while action mean remains misaligned.
```

## Row Outputs

Write:

```text
materialized_source_history_objective_rows.csv
history_projection_audit.csv
family_summary.csv
fold_summary.csv
summary.json
```

Required row columns:

```text
history_intervention_id
pair_id
source_run_id
source_row_id
original_pair_id
source_identity
source_family
fold
condition
probe_template
correct_history_id
wrong_history_id
preferred_candidate_id
rejected_candidate_id
preferred_steer
preferred_throttle
preferred_brake
rejected_steer
rejected_throttle
rejected_brake
logp_cp
logp_cr
logp_wp
logp_wr
correct_preference_margin
wrong_history_preference_margin
preferred_hidden_margin
rejected_hidden_margin
correct_preference_loss
wrong_history_preference_loss
combined_loss
history_action_l2
correct_distance_to_preferred
correct_distance_to_rejected
wrong_distance_to_preferred
wrong_distance_to_rejected
correct_closer_to_preferred
wrong_closer_to_rejected
finite
```

## Summary Metrics

Required summary fields:

```text
row_count
finite_row_count
projection_valid_count
wrong_history_valid_count
source_identity_duplicate_count
active_quarantine_rows_used
checkpoint_sha256_before
checkpoint_sha256_after
checkpoint_weights_mutated
exact_objective_finite
correct_preference_loss_mean
wrong_history_preference_loss_mean
combined_loss_mean
correct_preference_positive_fraction
wrong_history_preference_positive_fraction
both_directional_fraction
correct_closer_to_preferred_fraction
wrong_closer_to_rejected_fraction
both_distance_directional_fraction
history_action_l2_mean
history_action_l2_p10
history_action_l2_p50
history_action_l2_p90
family_count
fold_count
worst_family_both_directional_fraction
worst_fold_both_directional_fraction
```

Expected structural values for M1339:

```text
row_count: 1376
wrong_history_valid_count: 1376
active_quarantine_rows_used: 0
checkpoint_weights_mutated: false
```

High or weak losses are not implementation failures. They are the residual that
later objective-only work may try to reduce.

## Immutability And Contract Checks

M1339 must:

```text
load checkpoint in eval mode;
verify P0 72-dim human-view online recurrent encoder contract;
verify response indices 0-11 and context indices 12-71;
compute checkpoint sha256 before and after;
report checkpoint_weights_mutated;
avoid optimizer construction;
avoid torch backward;
avoid parameter writes;
write labels_enter_actor_input=false;
```

If the checkpoint is incompatible, result class should be:

```text
materialized_source_history_objective_evaluator_contract_failure
```

## Result Classes

Use:

```text
materialized_source_history_objective_evaluator_pass
materialized_source_history_objective_evaluator_contract_failure
materialized_source_history_objective_evaluator_join_failure
materialized_source_history_objective_evaluator_nonfinite
materialized_source_history_objective_evaluator_mutation_failure
```

Pass condition:

```text
row_count == 1376
finite_row_count == 1376
projection_valid_count == 1376
wrong_history_valid_count == 1376
exact_objective_finite == true
checkpoint_weights_mutated == false
active_quarantine_rows_used == 0
```

## M1339 Implementation Plan

Add:

```text
src/autodrift/materialized_source_history_objective_evaluator.py
tests/test_materialized_source_history_objective_evaluator.py
docs/m1339-paper-route-materialized-source-history-objective-evaluator-implementation.md
```

Implementation command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.materialized_source_history_objective_evaluator \
  --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --corpus-run-dir runs/m1336_materialized_source_history_objective_corpus_export \
  --run-dir runs/m1339_materialized_source_history_objective_evaluator \
  --device cpu
```

Focused test command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_materialized_source_history_objective_evaluator.py
```

## What M1339 Must Not Do

M1339 must not:

```text
train;
run PPO;
update actor parameters;
interpolate checkpoints;
run public replay gates;
promote;
use private holdout;
add source labels or hidden parameters to actor inputs;
include quarantined halfshaft/global-friction rows in the active objective;
claim self-identification or driver performance.
```

## Decision

Admit one implementation milestone:

```text
m1339-paper-route-materialized-source-history-objective-evaluator-implementation
```

The implementation should produce finite exact full-corpus residuals first.
Only after that result is audited should the project consider objective-only
updates.
