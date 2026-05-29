# M1555 Paper-Route Temporal Active-Set Redesign Design

## Summary

M1555 designs the next route after M1553/M1554 showed that pair expansion alone
does not produce history-sensitive terminal-boundary effects.

Decision:

```text
temporal_active_set_redesign_admit_bounded_anchor_sensitivity_miner
```

The core change is:

```text
before running another wrong-history intervention,
first mine anchors where small local action perturbations can still change
terminal margin or success.
```

M1553 proved that the M1550 anchors replay cleanly, but history swaps do not
matter there. The next source criterion must therefore be temporal active-set
membership, not only pairability.

No implementation smoke, history intervention, candidate materialization,
training corpus export, training, PPO, promotion, private holdout, actor-input
change, or level3 self-identification claim is admitted by M1555.

## Why Redesign The Active Set

M1553 result:

```text
accepted_pair_count: 21
intervention_row_count: 420
anchor_replay_failure_count: 0
passes_public_smoke_gates: true
terminal_max_history_margin_gap: 0.00025038157254009263
terminal_wrong_history_positive_target_sides: 0
terminal_donor_plus_hidden_positive_target_sides: 0
terminal_wrong_or_donor_success_drop_count: 0
```

This falsifies the narrow explanation that M1547 was null only because it had
too few pairs. The pair set is now broad enough to test, and the effect remains
null. The likely issue is that the chosen anchors are already in a stable basin
or too late in the maneuver.

## M1556 Scope

M1556 should implement a no-training local action-sensitivity miner. It must
not run history interventions.

Planned anchor windows:

```text
reveal
reveal_plus_4
decision_minus_16
decision_minus_8
decision
post_decision_8
```

Planned one-step local action overrides:

```text
steer_left
steer_right
brake_more
brake_less
steer_left_brake_more
steer_right_brake_more
```

Each candidate anchor should record:

```text
normal terminal margin;
override terminal margin;
local terminal margin gap;
success flip;
collision flip;
source family;
anchor window;
anchor step;
baseline action;
override action;
scene/current-state trace metadata;
guardrail flags.
```

## Active-Set Criteria

An anchor is active-set positive if:

```text
max local terminal-margin gap >= 0.02
or
at least one local action override flips success/collision outcome
```

Preferred anchors:

```text
pre-decision anchors: reveal, reveal_plus_4, decision_minus_16, decision_minus_8;
near-boundary normal terminal margin: abs(margin) <= 0.10;
multiple override directions with nonzero effect;
source-family diversity;
not dominated by one anchor window.
```

The design explicitly does not say that action sensitivity equals
self-identification. It only establishes that the anchor is still causally
controllable enough to justify a later history-intervention test.

## M1556 Gates

Public smoke gates:

```text
anchor_candidate_count >= 64
local_perturbation_row_count >= 384
action_sensitive_anchor_count >= 12
predecision_sensitive_anchor_count >= 6
source_family_count >= 4
max_single_family_share <= 0.4
success_flip_count >= 2
guardrail_violation_count == 0
history_interventions_executed == false
candidate_materialized == false
training_started == false
ppo_used == false
private_holdout_used == false
actor_input_contract_changed == false
training_corpus_exported == false
level3_self_id_claim_made == false
```

Evidence-quality targets:

```text
action_sensitive_anchor_count >= 20
predecision_sensitive_anchor_count >= 10
active_anchor_window_count >= 3
active_source_family_count >= 4
max_single_active_family_share <= 0.35
```

## Required Artifacts

M1556 should write:

```text
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/source_spec_rows.csv
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/anchor_candidate_rows.csv
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/local_perturbation_rows.csv
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/accepted_active_anchor_rows.csv
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/source_family_summary.csv
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/window_summary.csv
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/guardrail_summary.csv
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/summary.json
```

Do not write:

```text
intervention_rows.csv
training corpus
checkpoint
promotion artifact
```

## Follow-Up Logic

If M1556 active-set gates pass:

```text
M1557 audits the active-set miner.
M1558 may design history interventions only over accepted active anchors.
```

If M1556 active-set gates fail:

```text
M1557 audits scenario_sampling_failure.
Do not replay wrong-history interventions on inactive anchors.
Route to broader task generation or branch synthesis.
```

## Guardrails

```text
candidate_materialized: false
training_started: false
evaluation_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1556-paper-route-temporal-active-set-anchor-sensitivity-miner-implementation
```
