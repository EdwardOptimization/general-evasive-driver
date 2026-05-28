# M1305 Paper-Route Source-History Concentration-Aware Refresh Design

## Summary

M1305 designs the next step after the M1304 failed-offset audit.

Decision:

```text
source_history_concentration_aware_refresh_design_admit_plan_builder
```

M1304 found a concentrated failure pattern:

```text
top_failed_probe_template: left_brake_probe, share 0.6086956522
top_failed_source_family_pair: single_wheel_grip_collapse->single_wheel_grip_collapse, share 0.5652173913
top_failed_source_fault_pair: rear_left_grip_collapse->rear_right_grip_collapse, share 0.5652173913
top_failed_pair_id_share: 0.0869565217
```

The next step should not train immediately. First build a deterministic
concentration-aware refresh plan that rebalances public split folds and defines
bounded source-family/probe-template weights without targeting one pair ID.

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
threshold relaxation, high-fidelity validation claim, paper-level claim, or
self-identification claim occurs in M1305.

## Diagnosis

The M1304 evidence says:

```text
not a single pair artifact;
not a mutation guard failure;
not a PPO issue;
not a closed-loop driver result;
compatible with corpus/objective imbalance by source family and probe template.
```

The failure mode to address is:

```text
source-history trainable-scope update learns a useful directional signal on
some pair-disjoint splits, but the signal is weaker when eval folds are
dominated by single-wheel grip-collapse and left-brake probe groups.
```

## Design

M1306 should implement a no-training plan builder:

```text
python -m autodrift.source_history_concentration_refresh_plan
```

Inputs:

```text
runs/m1302_source_history_trainable_scope_repeat_probe/*
runs/m1304_source_history_repeat_failed_offset_audit/*
```

Outputs:

```text
runs/m1306_source_history_concentration_refresh_plan/summary.json
runs/m1306_source_history_concentration_refresh_plan/balanced_split_rows.csv
runs/m1306_source_history_concentration_refresh_plan/group_weight_rows.csv
runs/m1306_source_history_concentration_refresh_plan/fold_composition_summary.csv
```

The plan builder should not load a model or update any checkpoint.

## Split Refresh

The split refresh should assign pair IDs to deterministic public folds while
balancing group composition. The balancing keys are:

```text
source_family_pair
source_fault_pair
probe_template
margin_bucket from M1304 group_min_margin
```

Required invariants:

```text
pair-disjoint train/eval folds;
all folds nonempty;
each fold contains both probe templates;
each fold contains at least two source_family_pair values when the corpus allows;
no fold is selected or tuned as a private holdout;
no pair_id-specific objective weight is allowed.
```

Margin buckets:

```text
deep_negative: group_min_margin < -1.0
negative: -1.0 <= group_min_margin < -0.05
near_boundary: -0.05 <= group_min_margin < 0.0
positive: group_min_margin >= 0.0
```

The planner should report fold imbalance, not hide it. If the corpus is too
small to balance all keys, M1306 should classify that as corpus-insufficient
and route to source corpus expansion instead of pretending the plan is robust.

## Weight Refresh

The weight plan should be group-level, not row- or pair-ID-specific.

Allowed weight components:

```text
inverse source_family_pair frequency;
inverse probe_template frequency;
failed-concentration boost for source_family_pair x probe_template combinations;
small near-boundary boost from margin_bucket;
cap and normalize weights to avoid one public surface dominating.
```

Forbidden:

```text
pair_id-specific weights;
history_intervention_id-specific weights;
offset-specific weights that only repair offsets 2 and 4;
private holdout feedback;
actor input changes.
```

Initial suggested caps:

```text
max_group_weight: 2.0
min_group_weight: 0.5
failed_combo_boost_cap: 1.5
near_boundary_boost_cap: 1.25
```

The top M1304 failed combo should receive pressure, but not exclusive pressure:

```text
single_wheel_grip_collapse->single_wheel_grip_collapse x left_brake_probe
```

The right-brake companion and non-grip-collapse families should still appear in
the objective so the next update does not become a one-combo repair.

## Next Implementation Gate

M1306 should pass only if:

```text
balanced_split_rows.csv exists;
group_weight_rows.csv exists;
fold_composition_summary.csv exists;
pair-disjoint folds are preserved;
no pair_id-specific weight is used;
max group weight <= 2.0;
all folds have both probe templates;
fold composition improves over M1302 hash splits on at least one concentration metric;
PPO, training, private holdout, promotion, and actor-input changes remain unused.
```

M1306 should not train a policy. It only builds the plan and reports whether the
plan is admissible.

## Later Probe Gate

Only after M1306 passes should a bounded weighted repeat be admitted.

Suggested M1307 or later pass criteria for a weighted `fusion_head` repeat:

```text
offset_pass_count >= 3/5;
mean eval row/group directional fractions >= 0.25;
mean full both-positive rows >= 38.0;
mean full all-rows-both-positive groups >= 19.0;
top failed source-family/probe combo improves versus M1302/M1304;
no forbidden parameter group mutation;
no PPO, promotion, private holdout, threshold relaxation, or actor-input change.
```

If the weighted repeat improves only the concentrated combo while hurting global
metrics, route to objective tradeoff audit. If it does not improve the combo,
route to branch synthesis or sequence/trajectory preference targets.

## Public-Row Overfit Risk

Risk:

```text
high enough to require caps and no pair-specific weights
```

M1304 uses public diagnostic rows. It is valid to use them for process repair,
but not to claim paper-grade generalization. The design therefore limits the
next implementation to public plan construction and bounded diagnostic rerun.

## Guardrails

M1305 preserves:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
self_identification_claimed: false
```

## Decision

Admit M1306:

```text
m1306-paper-route-source-history-concentration-refresh-plan
```

M1306 should implement and run the no-training concentration-aware plan builder.
PPO and promotion remain blocked.
