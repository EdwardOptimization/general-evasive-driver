# M1278 Paper-Route Four-Wheel Source Intervention Materialization Result Audit

## Summary

M1278 audits the M1277 preferred/rejected source intervention artifacts.

Decision:

```text
four_wheel_source_intervention_materialization_audit_admit_response_history_design
```

M1277 is infrastructure-valid and artifact-clean:

```text
intervention_rows: 202
observation_rows: 202
action_sequence_rows: 29088
observation_dim: 72
observation_all_finite: true
preferred_success_fail_count: 0
preferred_margin_negative_count: 0
margin_gap_below_threshold_count: 0
```

But M1277 is not directly suitable for policy training. The same current
human-view source observation can require different preferred actions under
hidden branch A or B. Without branch-specific response history, direct
behavior-cloning or actor training would create contradictory labels.

Therefore the next step should design response-history materialization, not
policy training.

## Evidence

Primary artifacts:

```text
runs/m1277_four_wheel_source_intervention_materialization/summary.json
runs/m1277_four_wheel_source_intervention_materialization/intervention_rows.csv
runs/m1277_four_wheel_source_intervention_materialization/intervention_observations.csv
runs/m1277_four_wheel_source_intervention_materialization/intervention_action_sequences.csv
runs/m1277_four_wheel_source_intervention_materialization/source_pair_rows.csv
```

Guardrails held:

```text
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```

## Observation Cleanliness

`intervention_observations.csv` has:

```text
columns: 73
schema: intervention_id + obs_0 ... obs_71
forbidden observation fields: none
all finite: true
```

Forbidden fields checked absent from observation columns:

```text
fault
condition
candidate
success
margin
subset
source
label
```

Interpretation:

```text
M1277 keeps source labels and outcomes outside actor-view observations.
```

## Outcome Quality

Intervention rows:

```text
near_high_union: 76
family_balanced: 126
condition A: 101
condition B: 101
```

Preferred outcomes:

```text
preferred_terminal_reason obstacle_completed: 202
preferred_success_fail_count: 0
preferred_margin_negative_count: 0
```

Rejected outcomes:

```text
rejected_success true: 150
rejected_success false: 52
rejected_terminal_reason obstacle_completed: 150
rejected_terminal_reason collision: 48
rejected_terminal_reason horizon: 4
```

Margin gap:

```text
min: 0.0242185615
median: 0.0613144851
p90: 0.3798025288
max: 0.8165994033
margin_gap_below_0.02: 0
```

Interpretation:

```text
M1277 contains both success-drop counterfactuals and lower-margin success
counterfactuals. This is suitable as source-intervention material.
```

## Why Direct Policy Training Is Blocked

M1277 intentionally creates rows where:

```text
same visible source observation
condition A prefers action A
condition B prefers action B
```

That is the source of the self-identification problem, not a deployable policy
input.

If we train a memoryless/current-frame actor directly on these rows, the labels
are contradictory. If we train a recurrent actor without branch-specific
history, the branch is still invisible. Giving branch labels or fault metadata
to the actor would violate the human-view contract.

Therefore the next missing artifact is:

```text
branch-specific command-response history
```

The future actor should disambiguate branches from:

```text
previous commands
actuator state
ego/IMU-like response
short response history
```

not from fault labels.

## Next Step

Admit design-only:

```text
m1279-paper-route-four-wheel-source-response-history-materialization-design
```

M1279 should design no-training history artifacts that pair each intervention
with branch-specific response history:

```text
history_prefix_rows.csv
history_frame_rows.csv
history_intervention_rows.csv
wrong_history_pair_rows.csv
summary.json
```

The design must define:

```text
what fixed probing / natural command prefix is used;
which response fields enter history;
how branch A/B histories attach to the same current intervention observation;
how wrong-history swaps are represented;
how to keep branch/fault labels out of actor-view observations;
how to audit whether histories are distinguishable without using labels.
```

## Decision

Do not train.

Do not run PPO.

Do not promote.

Do not integrate into actor/Gym yet.

Do not do direct BC from M1277 rows.

Route to response-history materialization design:

```text
experiments/manifests/m1279-paper-route-four-wheel-source-response-history-materialization-design.json
```
