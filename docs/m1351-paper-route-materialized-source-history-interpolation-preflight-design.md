# M1351 Paper-Route Materialized Source-History Interpolation Preflight Design

## Summary

M1351 designs a trust-region interpolation preflight for the M1346 update
direction after raw M1346 failed M267/M264 replay in M1349.

Decision:

```text
materialized_source_history_interpolation_preflight_design_admit_implementation
```

This is design-only. It does not create checkpoints, run replay, train, run PPO,
use private holdout, change actor inputs, or promote.

## Question

M1346 produced a useful fixed-objective direction:

```text
combined_loss_mean: 6.8847534022 -> 1.9998926339
group_min_joint_margin_mean: -6.8026667906 -> -1.1251848645
```

But raw M1346 destroyed the first replay proof surface:

```text
M267/M264 normal success: 1.0 -> 0.0
success-drop count: 17 -> 0
normal_margin_mean_delta: -0.1065894892
```

M1352 should answer:

```text
Does the M1154 -> M1346 direction have any small-alpha region that keeps exact
source-history objective lift while retaining M267/M264 replay?
```

## Candidate Alphas

Use a conservative ladder:

```text
0.005
0.010
0.020
0.050
0.100
0.200
```

Also record reference rows:

```text
0.000 = M1154 base reference
1.000 = raw M1346 reference, no need to rerun replay because M1349 already
        established first-surface failure
```

Do not add a dense alpha sweep until this sparse ladder is audited.

## Interpolation Semantics

Create candidate checkpoints:

```text
theta_alpha = theta_M1154 + alpha * (theta_M1346 - theta_M1154)
```

Allowed changed parameters:

```text
actor_mean.bias
actor_mean.weight
response_context_fusion.0.bias
response_context_fusion.0.weight
```

Required guard:

```text
all non-allowed parameter deltas must be zero;
log_std_l2 must be zero;
actor input config must equal the M1154 base;
checkpoint contract must remain canonical_72_human_view_online_recurrent.
```

Implementation may reuse `interpolate_full_state` style full-state
interpolation, but it must verify that forbidden tensors do not change. Because
raw M1346 already passed the mutation guard, full-state interpolation is safe
only if this verification passes.

## Exact Metric Tier

For every alpha checkpoint, run:

```text
autodrift.materialized_source_history_objective_evaluator
autodrift.materialized_source_history_pair_group_metrics
```

Record:

```text
combined_loss_mean
group_min_joint_margin_mean
group_one_sided_conflict_count
group_all_rows_both_directional_count
group_both_negative_count
eval_fold_4_group_min_joint_margin_mean
forbidden_parameter_mutation_detected
log_std_l2
```

Exact-objective admission for replay:

```text
combined_loss_mean < M1154 combined_loss_mean
group_min_joint_margin_mean > M1154 group_min_joint_margin_mean
eval_fold_4_group_min_joint_margin_mean >= M1154 eval fold 4 group_min_joint_margin_mean
forbidden_parameter_mutation_detected == false
log_std_l2 == 0
```

Do not require `group_all_rows_both_directional_count` to improve for replay
admission, because raw M1346 showed that this count can improve while replay
collapses. Treat it as diagnostic only.

## Replay Tier

Run replay only for exact-admitted nonzero alphas.

First replay surface:

```text
M267/M264
```

Use:

```text
autodrift.boundary_outcome_replay_gate
corpus: runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
env_config: configs/m121_human_view_zero_obstacle_relvel.json
max_continuation_steps: 60
max_normal_success_drop: 0.0
max_normal_margin_regression: 0.005
max_margin_gap_regression: 0.001
max_success_drop_count_regression: 0
```

Only if an alpha passes M267/M264, run:

```text
M183/M170
```

with the same tolerances and:

```text
corpus: runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv
```

Stop once all exact-admitted alphas have M267/M264 outcomes and all
M267-passing alphas have M183/M170 outcomes. Do not run full public replay in
M1352.

## Candidate Decision

M1352 should select:

```text
largest alpha that:
  exact-admitted == true
  M267/M264 gate_pass == true
  M183/M170 gate_pass == true if M183/M170 was required
```

If multiple candidates pass, prefer the largest alpha because it preserves more
of the exact objective improvement while still satisfying replay preflight.

Result classes:

```text
materialized_source_history_interpolation_preflight_pass
materialized_source_history_interpolation_preflight_no_exact_candidate
materialized_source_history_interpolation_preflight_m267_proof_washout
materialized_source_history_interpolation_preflight_m183_proof_washout
materialized_source_history_interpolation_preflight_contract_artifact
```

## Route Rules

If no alpha improves exact metrics:

```text
route to objective redesign audit
```

If at least one alpha improves exact metrics but none pass M267/M264:

```text
route to replay-aware active-set repair design
```

If an alpha passes M267/M264 but fails M183/M170:

```text
route to boundary-cliff active-set repair design
```

If an alpha passes both:

```text
route to limited repeat or full public replay design, not promotion
```

## Required M1352 Artifacts

```text
runs/m1352_materialized_source_history_interpolation_preflight/summary.json
runs/m1352_materialized_source_history_interpolation_preflight/alpha_summary.csv
runs/m1352_materialized_source_history_interpolation_preflight/candidate_checkpoints.csv
runs/m1352_materialized_source_history_interpolation_preflight/checkpoints/*.pt
docs/m1352-paper-route-materialized-source-history-interpolation-preflight.md
```

`alpha_summary.csv` must include both exact metrics and replay outcomes so the
tradeoff is visible in one table.

## Blocked Routes

Do not:

```text
run PPO;
promote any alpha;
use private holdout;
run full public replay;
change actor inputs;
relax replay thresholds;
claim driver performance;
claim strong self-identification.
```

## Decision

M1351 admits:

```text
m1352-paper-route-materialized-source-history-interpolation-preflight
```

M1352 may create interpolated checkpoints and run exact plus two-surface replay
preflight. It must not train, run PPO, use private holdout, or promote.
