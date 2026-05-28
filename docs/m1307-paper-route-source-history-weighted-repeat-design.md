# M1307 Paper-Route Source-History Weighted Repeat Design

## Summary

M1307 designs the bounded weighted repeat protocol that would consume the
M1306 concentration refresh plan.

Decision:

```text
source_history_weighted_repeat_design_route_to_branch_synthesis
```

The next implementation should not start yet. The trainable-scope escalation
branch has reached its synthesis cadence, so the next milestone must synthesize
M1298-M1307 before opening an implementation branch.

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
threshold relaxation, high-fidelity validation claim, paper-level claim, or
self-identification claim occurs in M1307.

## Inputs

M1307 designs around:

```text
runs/m1306_source_history_concentration_refresh_plan/balanced_split_rows.csv
runs/m1306_source_history_concentration_refresh_plan/group_weight_rows.csv
runs/m1306_source_history_concentration_refresh_plan/fold_composition_summary.csv
```

M1306 admissibility:

```text
pair_disjoint: true
all_folds_nonempty: true
all_folds_have_both_probe_templates: true
pair_specific_weight_used: false
max_group_weight: 2.0
composition_improved: true
```

## Intended Implementation

The implementation should extend the existing no-PPO trainable-scope probe. It
should not create a new training stack.

Suggested CLI:

```bash
PYTHONPATH=src python -m autodrift.source_history_trainable_scope_probe \
  --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --history-run-dir runs/m1280_four_wheel_source_response_history_materialization \
  --intervention-run-dir runs/m1277_four_wheel_source_intervention_materialization \
  --run-dir runs/m13xx_source_history_weighted_repeat_probe \
  --device cpu \
  --steps 400 \
  --lr 0.0002 \
  --target-margin 0.05 \
  --scopes fusion_head \
  --split-plan runs/m1306_source_history_concentration_refresh_plan/balanced_split_rows.csv \
  --group-weight-rows runs/m1306_source_history_concentration_refresh_plan/group_weight_rows.csv \
  --split-offsets 0,1,2,3,4
```

Required behavior:

```text
use assigned_eval_fold from balanced_split_rows.csv instead of hash buckets;
apply group_weight by pair_id/probe_template group;
propagate weights into row-level correct/wrong losses and group floor loss;
keep parameter mutation guards unchanged;
save weighted objective metadata into summary.json;
write weighted directional/group artifacts with split_fold and group_weight.
```

## Weight Rules

Allowed:

```text
group-level weight by source_family_pair/probe_template/margin_bucket;
capped weights from M1306 group_weight_rows.csv;
same weight for both rows in a pair_id/probe_template group.
```

Forbidden:

```text
pair_id-specific weights;
history_intervention_id-specific weights;
offset-only weights;
private holdout feedback;
actor input changes.
```

Hard checks:

```text
pair_specific_weight_used == false
max_group_weight <= 2.0
min_group_weight >= 0.5
all train/eval folds remain pair-disjoint
```

## Pass Criteria

A future weighted repeat may pass only if all of the following hold:

```text
forbidden_parameter_mutation_detected == false
offset_pass_count >= 3/5
mean_eval_both_directional_fraction >= 0.25
mean_eval_group_all_rows_both_positive_fraction >= 0.25
mean_full_both_positive_count >= 38.0
mean_full_group_all_rows_both_positive_count >= 19.0
```

The full-count thresholds intentionally use M1302 means, not the older weaker
M1295 thresholds, so the weighted protocol cannot win by sacrificing the
unweighted repeat evidence.

Concentration-specific check:

```text
top failed source-family/probe combo failure fraction must improve over M1304.
```

The primary combo is:

```text
single_wheel_grip_collapse->single_wheel_grip_collapse x left_brake_probe
```

If global repeat metrics pass but this combo does not improve, the result is a
tradeoff artifact and must route to audit, not promotion or PPO.

## Output Requirements

A future weighted repeat should write:

```text
summary.json
scope_summaries.csv
repeat_summaries.csv
split_rows.csv
directional_rows.csv
group_rows.csv
parameter_group_delta.csv
weighted_group_diagnostics.csv
```

The summary must record:

```text
split_plan_used: true
group_weights_used: true
pair_specific_weight_used: false
max_group_weight
weighted_loss_enabled: true
top_failed_combo_improved
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
```

## Synthesis Requirement

Do not implement the weighted repeat immediately after M1307.

Next:

```text
m1308-paper-route-source-history-trainable-scope-escalation-synthesis
```

M1308 must synthesize M1298-M1307 and decide whether to:

```text
promote to a new weighted-repeat implementation branch;
pivot to source corpus expansion;
pivot to sequence/trajectory preference targets;
or stop this public-row source-history branch.
```

This prevents the branch from becoming a long local loop around fixed public
diagnostic rows.

## Guardrails

M1307 preserves:

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
