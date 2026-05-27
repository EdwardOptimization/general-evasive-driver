# M1118 V4 Public Base Failed Wrong-History Retention Actor-Update Probe

## Purpose

M1118 runs the retention-aware actor-coupling probe admitted by M1117.

This milestone runs only the bounded optimizer candidates and pre-replay audits.
It does not run PPO, replay gates, promotion, private holdout, or actor-input
changes.

## Inputs

Base checkpoint:

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

Objective and retention artifacts:

```text
runs/m1107_materialized_objective_corpus/boundary_outcome_corpus.npz
runs/m1115_materialized_failed_wrong_history_retention_export/combined_target_base_rejected_anchor.npz
runs/m1115_materialized_failed_wrong_history_retention_export/target_base_rejected_trajectory_anchor.npz
```

Candidate recipe:

```text
seeds: 111800, 111801, 111802
steps: 10
learning_rate: 0.000025
train_scope: actor_coupling
train_log_std: false
trajectory_action_anchor_coef: 250.0
```

## Result

All three candidates pass the pre-replay gates:

```text
result_class: failed_wrong_history_retention_actor_update_exact_candidate
candidate_count: 3
pre_replay_pass_count: 3
best_seed: 111800
best_checkpoint: runs/m1118_failed_wrong_history_retention_actor_update_seed111800/optimized_checkpoint.pt
best_loss_mean_improvement: 0.003012359
best_target_base_only_trajectory_anchor_mse: 0.000001498
```

Candidate summary:

```text
seed111800:
  exact loss improvement: 0.003012359
  action anchor MSE: 0.000003189
  snippet anchor MSE: 0.000008581
  combined trajectory MSE: 0.000005781
  target-base-only trajectory MSE: 0.000001498

seed111801:
  exact loss improvement: 0.003008902
  action anchor MSE: 0.000004039
  snippet anchor MSE: 0.000008658
  combined trajectory MSE: 0.000005980
  target-base-only trajectory MSE: 0.000001715

seed111802:
  exact loss improvement: 0.002998769
  action anchor MSE: 0.000003341
  snippet anchor MSE: 0.000008643
  combined trajectory MSE: 0.000005924
  target-base-only trajectory MSE: 0.000001662
```

All anchor MSE values are below the registered `0.0001` threshold.

## Parameter Audit

All candidates changed exactly the allowed actor-coupling tensors:

```text
response_context_fusion.0.weight
response_context_fusion.0.bias
actor_mean.weight
actor_mean.bias
```

No candidate changed `log_std`, `response_encoder.*`, `context_encoder.*`,
`gru.*`, `critic.*`, or actor-input contract metadata.

## Artifacts

Primary artifacts:

```text
runs/m1118_failed_wrong_history_retention_actor_update_probe/summary.json
runs/m1118_failed_wrong_history_retention_actor_update_probe/candidate_summary.csv
runs/m1118_failed_wrong_history_retention_actor_update_probe/parameter_audit.csv
runs/m1118_failed_wrong_history_retention_actor_update_anchor_audit/combined/summary.json
runs/m1118_failed_wrong_history_retention_actor_update_anchor_audit/target_base_only/summary.json
```

Candidate run directories:

```text
runs/m1118_failed_wrong_history_retention_actor_update_seed111800
runs/m1118_failed_wrong_history_retention_actor_update_seed111801
runs/m1118_failed_wrong_history_retention_actor_update_seed111802
```

## Interpretation

M1118 shows that the M1115 retention anchor does not block useful exact M1107
objective movement. Compared with M1110, this probe adds direct closed-loop
wrong-history trajectory retention and keeps target-base-only retention error
small.

This is still not driver improvement evidence. It is a pre-replay candidate
result. The candidate must next face old public replay, source-diverse replay,
family-intersection replay, and behavior gates. No replay or promotion happened
in M1118.

## Decision

```text
failed_wrong_history_retention_actor_update_exact_candidate_route_to_first_replay_design
```

Next milestone:

```text
m1119-v4-public-base-failed-wrong-history-retention-first-replay-design
```
