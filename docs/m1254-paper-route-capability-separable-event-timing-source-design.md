# M1254 Paper-Route Capability-Separable Event-Timing Source Design

## Summary

M1254 opens an event-timing/source-state source branch after M1253 stopped
same-source trajectory proposal budget expansion.

Decision:

```text
event_timing_source_design_admit_bounded_smoke
```

M1250-M1252 showed that trajectory proposals can find branch-specific action
differences, but the sampled state is slightly too late or too tight:

```text
pair 5 step: 24
pair 5 obstacle_distance: about 6.92 m
M1252 pair_min_best_margin: -0.0006610772
```

The next hypothesis is that accepted capability-separable rows may exist in
nearby emergency timing states: early enough for each branch to have a viable
own maneuver, but late enough that the wrong branch's maneuver loses margin.

## Source Variables

M1255 should vary source-state timing, not policy inputs:

```text
min_step
snapshot_stride
max_snapshots_per_scenario
obstacle_longitudinal_min
obstacle_longitudinal_max
target_min_best_margin
target_max_best_margin
```

The first smoke should use a denser timing window around the observed near-miss:

```text
source_min_step: 18
source_snapshot_stride: 2
source_max_snapshots_per_scenario: 8
source_obstacle_longitudinal_min: 4.0
source_obstacle_longitudinal_max: 24.0
target_min_best_margin: 0.002
target_max_best_margin: 0.06
```

This is not threshold relaxation. The accepted-source criteria remain:

```text
own-branch best margins must be >= 0.0
min_cross_regret_margin remains 0.02
min_best_action_l2 remains 0.12
```

## Implementation Route

M1255 should add CLI overrides to the source constructor instead of creating a
new actor or new environment contract:

```text
--source-min-step
--source-max-steps
--source-snapshot-stride
--source-max-snapshots-per-scenario
--source-obstacle-longitudinal-min
--source-obstacle-longitudinal-max
```

These override source-corpus collection only. They must not enter actor
observations.

The existing `trajectory_proposal` candidate mode should be reused:

```text
candidate_mode: trajectory_proposal
sequence_length: 4
proposal_count_per_condition: 24
proposal_seed: 125500
```

## Acceptance Gates

M1255 source-positive rows require:

```text
best_A_success == true
best_B_success == true
margin_A_best_A >= 0.0
margin_B_best_B >= 0.0
normalized_l2(best_A_vector, best_B_vector) >= 0.12
cross_regret_A >= 0.02
cross_regret_B >= 0.02
```

Diagnostics that may be reported but not accepted:

```text
one-sided regret
near-positive nonviable rows
near-boundary action-equivalent rows
reset-only or current-frame-only effects
```

## Runtime Bounds

M1255 remains an infrastructure smoke:

```text
seed_count: 4
max_pairs: 8
max_pairs_per_seed: 4
max_pairs_per_family_pair: 8
max_relocation_candidates: 12
proposal_count_per_condition: 24
max_continuation_steps: 18
```

If it is too slow, reduce pairs first. Do not silently turn it into a long
source-mining run.

## Artifacts

Required M1255 artifacts:

```text
summary.json
snapshot_candidates.csv
matched_capability_pairs.csv
trajectory_proposals.csv
trajectory_proposal_rollouts.csv
relocation_candidates.csv
accepted_separable_pairs.csv
rejected_pairs.csv
fault_family_pair_summary.csv
model_fidelity_limits.md
```

Summary must include the effective source timing overrides:

```text
effective_min_step
effective_snapshot_stride
effective_max_snapshots_per_scenario
effective_obstacle_longitudinal_min
effective_obstacle_longitudinal_max
```

## Guardrails

M1254/M1255 does not change actor input:

```text
no timing labels in actor input
no proposal labels in actor input
no oracle outcomes in actor input
no hidden physical parameters in actor input
no training
no PPO
no promotion
no private holdout
no self-identification claim
```

## Next

Admit:

```text
m1255-paper-route-capability-separable-event-timing-source-smoke
```

If M1255 remains zero-accepted, audit before another source change. Do not keep
cycling event-timing variants without a synthesis decision.
