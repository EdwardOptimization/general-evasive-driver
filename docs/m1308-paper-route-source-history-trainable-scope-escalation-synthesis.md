# M1308 Paper-Route Source-History Trainable-Scope Escalation Synthesis

## Summary

M1308 synthesizes the M1298-M1307 trainable-scope escalation branch.

Synthesis decision:

```text
promote_to_next_branch
```

Decision:

```text
source_history_trainable_scope_escalation_synthesis_promote_to_weighted_repeat_implementation
```

The branch showed that widening from actor-mean-only to `response_context_fusion
+ actor_mean` exposes a real fixed-current source-history directional signal,
but the signal is not repeat-robust under the original hash splits. M1304-M1306
then identified and addressed the main split failure as source-family/probe
concentration, producing an admissible no-training balanced split and group
weight plan.

The next branch should implement a bounded weighted repeat. PPO, promotion,
private holdout use, paper-level claims, and closed-loop self-identification
claims remain blocked.

## Evidence Summary

M1298 designed a bounded no-PPO trainable-scope diagnostic because the earlier
actor-mean-only objective branch was underpowered.

M1299 produced the first strong trainable-scope signal:

```text
best_scope: fusion_head
eval_both_directional_fraction: 0.25
eval_group_all_rows_both_positive_fraction: 0.25
full_both_positive_count: 46/152
full_group_all_rows_both_positive_count: 23/76
forbidden_parameter_mutation_detected: false
```

M1300 accepted M1299 as meaningful but boundary-threshold evidence, not a PPO
or promotion result.

M1301 designed repeat/split robustness. M1302 ran it:

```text
offset_pass_count: 3/5
mean_eval_both_directional_fraction: 0.2335317460
mean_eval_group_all_rows_both_positive_fraction: 0.2335317460
mean_full_both_positive_count: 38.0
mean_full_group_all_rows_both_positive_count: 19.0
result_class: source_history_trainable_scope_repeat_mixed
```

M1303 audited that as split-sensitive mixed evidence.

M1304 found the failed offsets were concentrated:

```text
top_failed_probe_template: left_brake_probe, share 0.6086956522
top_failed_source_family_pair: single_wheel_grip_collapse->single_wheel_grip_collapse, share 0.5652173913
top_failed_pair_id_share: 0.0869565217
```

M1305 designed a concentration-aware refresh. M1306 implemented the no-training
plan:

```text
result_class: source_history_concentration_refresh_plan_admissible
pair_disjoint: true
all_folds_nonempty: true
all_folds_have_both_probe_templates: true
pair_specific_weight_used: false
max_group_weight: 2.0
original_max_source_family_pair_fold_share: 0.6666666667
balanced_max_source_family_pair_fold_share: 0.625
composition_improved: true
```

M1307 designed the bounded weighted repeat protocol and required branch
synthesis before implementation.

## Supported Claims

Supported:

```text
Actor-mean-only was underpowered for the source-history fixed-current
diagnostic.
```

Supported:

```text
The `fusion_head` scope can decode more source-history directionality than
actor_mean-only on the same corpus.
```

Supported:

```text
The signal is not a single split artifact. It passes 3/5 deterministic
pair-disjoint split offsets.
```

Supported:

```text
The repeat weakness is structured. Failed eval groups concentrate by
source-family/probe-template rather than one pair ID.
```

Supported:

```text
A no-training concentration-aware plan can preserve pair-disjoint folds, avoid
pair-specific weights, cap group weights, and improve source-family fold
balance.
```

## Falsified Claims

Falsified:

```text
The M1299 single-split strong result is already repeat-robust.
```

Falsified:

```text
The next step can safely be PPO continuation.
```

Falsified:

```text
The M1302 failure is just one stale pair ID.
```

Falsified:

```text
Fixed-current source-history diagnostics alone prove closed-loop online
self-identification.
```

Not yet proven:

```text
The weighted repeat will improve M1302 repeat robustness.
```

Not yet proven:

```text
The resulting candidate will preserve older closed-loop public proof gates.
```

## Failure Taxonomy Summary

Primary branch failure mode:

```text
scenario_sampling_failure risk
```

Reason:

```text
Original hash folds put disproportionate pressure on source-family/probe
combinations that the objective had not balanced.
```

Secondary risk:

```text
objective_overfit risk
```

Reason:

```text
The next weighted repeat will still use public diagnostic rows. It must keep
weights group-level and capped, and it must route to audit rather than PPO if it
only repairs the top public combo.
```

Not observed:

```text
contract_violation
training_instability
forbidden_parameter_mutation
private_holdout_contamination
promotion_gate_failure
```

## Public-Gate Overfit Risk

Risk:

```text
high
```

This branch operates on fixed public source-history diagnostic rows. That is
acceptable for mechanism development but not for paper-level generalization.
The next branch must keep claims local:

```text
fixed-current source-history weighted diagnostic only;
no closed-loop driver claim;
no PPO claim;
no private holdout claim;
no promotion claim.
```

The next branch must also preserve:

```text
no pair-specific weights;
max group weight <= 2.0;
pair-disjoint folds;
M1302 full-count retention thresholds.
```

## Next Branch Decision

Open a new branch:

```text
paper_route_source_history_weighted_repeat_implementation
```

Next milestone:

```text
m1309-paper-route-source-history-weighted-repeat-implementation
```

M1309 should implement the bounded weighted repeat protocol from M1307:

```text
extend source_history_trainable_scope_probe with --split-plan;
extend source_history_trainable_scope_probe with --group-weight-rows;
use assigned_eval_fold instead of hash buckets;
apply group weights to source-history losses;
preserve mutation guards;
run only no-PPO fusion_head weighted repeat.
```

M1309 should not promote, run PPO, use private holdout, relax thresholds, or
change actor inputs.

## Guardrails

M1308 preserves:

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
