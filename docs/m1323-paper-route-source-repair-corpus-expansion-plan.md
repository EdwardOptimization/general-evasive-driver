# M1323 Paper-Route Source Repair Corpus Expansion Plan

## Summary

M1323 ran the source-history corpus expansion plan builder on the M1322 source
repair corpus export.

Decision:

```text
source_repair_corpus_expansion_plan_gap_reported_route_to_result_audit
```

The M1322 source corpus is a major improvement over the old M1273 source corpus,
but it still does not fully meet the M1314 expansion target:

```text
planned_source_pairs: 216 / 240 target
planned_pair_probe_groups: 432 / 480 target
source_fault_family_count: 7 / 6 target
max_source_family_fold_share: 0.3260869565 / <=0.40 target
materialized_source_pair_count: 0
```

The plan is valid infrastructure. It is not yet an admission to source-history
materialization or PPO.

## Command

```bash
PYTHONPATH=src python -m autodrift.source_history_corpus_expansion_plan \
  --source-corpus-run-dir runs/m1322_source_repair_corpus_export \
  --history-run-dir runs/m1322_no_materialized_history \
  --run-dir runs/m1323_source_repair_corpus_expansion_plan \
  --target-source-pairs 240 \
  --fold-count 5
```

The empty/nonexistent `runs/m1322_no_materialized_history` path is intentional:
M1280 materialized histories belong to the old M1273 source run, and pair ids
can collide across source runs. M1323 therefore treats all M1322 rows as not yet
materialized.

## Result

Summary:

```text
result_class: source_history_corpus_expansion_plan_gap_reported
source_corpus_run_dir: runs/m1322_source_repair_corpus_export
history_run_dir: runs/m1322_no_materialized_history
target_source_pairs: 240
target_pair_probe_groups: 480
planned_source_pairs: 216
planned_pair_probe_groups: 432
source_fault_family_count: 7
corner_or_side_variant_count: 22
materialized_source_pair_count: 0
all_folds_nonempty: true
pair_disjoint: true
max_source_family_fold_share: 0.3260869565
pair_specific_weight_used: false
coverage_gap_reported: true
unsupported_or_undercovered_family_count: 5
```

## Family Coverage

Available families:

```text
single_wheel_grip_collapse: 62
steering_actuator_fault: 58
left_right_split_mu: 35
tire_blowout_like: 23
halfshaft_torque_loss: 22
single_wheel_brake_pull: 10
load_cg_perturbation: 6
```

Missing or under-target:

```text
global_friction_step: 0 / 30, missing
halfshaft_torque_loss: 22 / 30, under target
load_cg_perturbation: 6 / 30, under target
single_wheel_brake_pull: 10 / 30, under target
tire_blowout_like: 23 / 30, under target
```

## Fold Balance

Fold balance is now much better than M1315:

```text
M1315 max_source_family_fold_share: 0.5789473684
M1323 max_source_family_fold_share: 0.3260869565
```

Every fold is nonempty and pair-disjoint:

```text
all_folds_nonempty: true
pair_disjoint: true
```

Top family share per fold stays below the `0.40` target:

```text
fold 0: 0.3261, single_wheel_grip_collapse
fold 1: 0.2778, single_wheel_grip_collapse
fold 2: 0.3256, single_wheel_grip_collapse
fold 3: 0.2917, steering_actuator
fold 4: 0.3023, steering_actuator
```

## Interpretation

Supported:

```text
M1322 solves the source-family diversity and fold-balance problem that blocked
M1315.
```

Supported:

```text
No stale materialized histories were counted.
```

Still not supported:

```text
the corpus meets the full 240-pair / 480-pair-probe target;
global friction is represented;
source-history materialization can start without an audit;
PPO or policy-side objective tuning is admitted.
```

## Guardrails

Reported guardrails:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```

## Next Step

Admit one result audit:

```text
m1324-paper-route-source-repair-corpus-plan-result-audit
```

The audit should decide whether to:

```text
materialize source histories from the 216-row seven-family corpus now;
run a small targeted top-up source generation for under-target families;
or split global friction into a separate branch while using the seven-family corpus.
```

PPO and promotion remain blocked.
