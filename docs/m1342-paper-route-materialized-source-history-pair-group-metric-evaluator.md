# M1342 Paper-Route Materialized Source-History Pair-Group Metric Evaluator

## Summary

M1342 implemented and ran the no-update pair-group metric evaluator over the
M1339 materialized source-history objective rows.

Decision:

```text
materialized_source_history_pair_group_metrics_pass_route_to_result_audit
```

The group metric evaluator passes and confirms the M1340 two-condition conflict
as a group-level artifact.

## Implementation

Added:

```text
src/autodrift/materialized_source_history_pair_group_metrics.py
tests/test_materialized_source_history_pair_group_metrics.py
```

The tool reads M1339 row metrics and groups by:

```text
source_identity|probe_template
```

It does not load a checkpoint and does not rerun actor inference.

## Commands

Focused test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_materialized_source_history_pair_group_metrics.py
```

Result:

```text
1 passed in 2.02s
```

Group metrics:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.materialized_source_history_pair_group_metrics \
  --rows runs/m1339_materialized_source_history_objective_evaluator/materialized_source_history_objective_rows.csv \
  --run-dir runs/m1342_materialized_source_history_pair_group_metrics
```

## Artifacts

Primary artifacts:

```text
runs/m1342_materialized_source_history_pair_group_metrics/summary.json
runs/m1342_materialized_source_history_pair_group_metrics/group_rows.csv
runs/m1342_materialized_source_history_pair_group_metrics/family_group_summary.csv
runs/m1342_materialized_source_history_pair_group_metrics/fold_group_summary.csv
```

## Result

Structural metrics:

```text
result_class: materialized_source_history_pair_group_metrics_pass
row_count: 1376
group_count: 688
valid_two_condition_group_count: 688
```

Directional group metrics:

```text
group_all_rows_both_directional_count: 0
group_all_rows_distance_both_count: 0
group_one_sided_conflict_count: 684
group_both_negative_count: 4
group_all_rows_both_directional_fraction: 0.0
group_one_sided_conflict_fraction: 0.9941860465
group_both_negative_fraction: 0.0058139535
group_min_joint_margin_mean: -6.8026667906
```

Guardrails:

```text
checkpoint_loaded: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_update_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
labels_enter_actor_input: false
```

## Family Summary

Family group summary:

```text
left_right_split_mu: groups 74, one-sided 1.0, both-negative 0.0, group_min_joint_margin_mean -9.7974622507
load_cg_perturbation: groups 108, one-sided 1.0, both-negative 0.0, group_min_joint_margin_mean -6.2923381152
single_wheel_brake_pull: groups 124, one-sided 1.0, both-negative 0.0, group_min_joint_margin_mean -7.0384040263
single_wheel_grip_collapse: groups 128, one-sided 1.0, both-negative 0.0, group_min_joint_margin_mean -9.3712891461
steering_actuator_fault: groups 192, one-sided 0.9791666667, both-negative 0.0208333333, group_min_joint_margin_mean -4.2629899867
tire_blowout_like: groups 62, one-sided 1.0, both-negative 0.0, group_min_joint_margin_mean -6.2075619601
```

## Fold Summary

Fold group summary:

```text
fold 0: groups 142, one-sided 1.0, both-negative 0.0, group_min_joint_margin_mean -6.8638577117
fold 1: groups 140, one-sided 1.0, both-negative 0.0, group_min_joint_margin_mean -6.9133107909
fold 2: groups 136, one-sided 1.0, both-negative 0.0, group_min_joint_margin_mean -6.6405230042
fold 3: groups 136, one-sided 0.9852941176, both-negative 0.0147058824, group_min_joint_margin_mean -7.1400241045
fold 4: groups 134, one-sided 0.9850746269, both-negative 0.0149253731, group_min_joint_margin_mean -6.4443958161
```

## Interpretation

Supported:

```text
The M1340 conflict is exactly expressible as group-level metrics.
```

Supported:

```text
The group problem is broad across source families and folds, not an isolated
family or pair singleton.
```

Unsupported:

```text
The current checkpoint solves pair-group source-history directionality.
```

Unsupported:

```text
actor update;
PPO continuation;
promotion;
closed-loop driver performance;
paper-level evidence;
strong self-identification.
```

## Decision

Do not train.

Do not run PPO.

Do not update actor weights.

Do not promote.

Admit one result audit:

```text
m1343-paper-route-materialized-source-history-pair-group-metric-result-audit
```

M1343 should decide whether to route to bounded pair-group objective-update
design, source-current projection repair, or branch synthesis before further
implementation.
