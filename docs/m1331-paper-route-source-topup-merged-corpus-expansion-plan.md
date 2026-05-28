# M1331 Paper-Route Source Top-Up Merged Corpus Expansion Plan

## Summary

M1331 ran the source-history corpus expansion planner on the M1330 merged source
export.

Decision:

```text
source_topup_merged_corpus_expansion_plan_admissible_route_to_materialization_design
```

The merged corpus clears the main planning targets:

```text
planned_source_pairs: 366 / 240 target
planned_pair_probe_groups: 732 / 480 target
source_fault_family_count: 7
all_folds_nonempty: true
pair_disjoint: true
max_source_family_fold_share: 0.2739726027
materialized_source_pair_count: 0
```

This admits a source-history materialization design. It does not admit PPO,
promotion, or policy objective tuning yet.

## Command

```bash
PYTHONPATH=src python -m autodrift.source_history_corpus_expansion_plan \
  --source-corpus-run-dir runs/m1330_source_topup_additive_merge_export \
  --history-run-dir runs/m1330_no_materialized_history \
  --run-dir runs/m1331_source_topup_merged_corpus_expansion_plan \
  --target-source-pairs 240 \
  --fold-count 5
```

The nonexistent `runs/m1330_no_materialized_history` path is intentional. It
prevents stale materialized histories from earlier source runs being counted by
pair id.

## Result

Summary:

```text
result_class: source_history_corpus_expansion_plan_admissible
planned_source_pairs: 366
planned_pair_probe_groups: 732
source_fault_family_count: 7
corner_or_side_variant_count: 34
materialized_source_pair_count: 0
all_folds_nonempty: true
pair_disjoint: true
max_source_family_fold_share: 0.2739726027
pair_specific_weight_used: false
target_source_pairs_met: true
target_pair_probe_groups_met: true
target_source_family_count_met: true
coverage_gap_reported: true
unsupported_or_undercovered_family_count: 2
recommended_next_step: route to source-history materialization design
```

## Family Coverage

Available families:

```text
steering_actuator_fault: 96
single_wheel_grip_collapse: 64
single_wheel_brake_pull: 62
load_cg_perturbation: 54
left_right_split_mu: 37
tire_blowout_like: 31
halfshaft_torque_loss: 22
```

Missing or under target:

```text
global_friction_step: 0 / 30, missing
halfshaft_torque_loss: 22 / 30, under target
```

## Fold Balance

Fold balance is within target:

```text
max_source_family_fold_share: 0.2739726027 / <=0.40 target
```

Each fold contains all seven available source families:

```text
fold 0: 148 pair-probe groups, 7 families, top share 0.2162
fold 1: 146 pair-probe groups, 7 families, top share 0.2740
fold 2: 146 pair-probe groups, 7 families, top share 0.2740
fold 3: 146 pair-probe groups, 7 families, top share 0.2740
fold 4: 146 pair-probe groups, 7 families, top share 0.2740
```

## Interpretation

Supported:

```text
The M1330 merged source export is broad enough for source-history
materialization planning.
```

Supported:

```text
The M1330 global pair-id reindexing works with the planner: pair-disjoint folds
are valid and no stale materialized histories are counted.
```

Still unsupported:

```text
global friction coverage;
halfshaft reaching the per-family 30-row target;
source-history materialization artifacts;
policy-side source-history objective improvement;
PPO or promotion.
```

## Guardrails

Guardrails held:

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

Admit:

```text
m1332-paper-route-source-topup-materialization-design
```

Scope:

```text
design materialization from M1330/M1331 artifacts;
preserve source_run_id/source_row_id/original_pair_id metadata;
materialize command-response histories only after design;
do not train;
do not run PPO;
do not promote.
```
