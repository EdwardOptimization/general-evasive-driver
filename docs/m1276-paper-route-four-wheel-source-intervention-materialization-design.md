# M1276 Paper-Route Four-Wheel Source Intervention Materialization Design

## Summary

M1276 designs the first milestone in the new
`paper_route_four_wheel_source_intervention_materialization` branch.

Decision:

```text
four_wheel_source_intervention_materialization_design_admit_implementation
```

Admit next bounded no-training implementation:

```text
m1277-paper-route-four-wheel-source-intervention-materialization
```

This is design-only. No training, PPO, checkpoint promotion, private holdout,
actor-input expansion, accepted-threshold relaxation, high-fidelity validation
claim, paper-level claim, driver-performance claim, or self-identification claim
occurs in M1276.

## Objective

Convert M1273 source-corpus rows into explicit preferred/rejected
counterfactual artifacts:

```text
same visible source state
same human-view observation
hidden branch A or B
preferred action sequence for that branch
rejected cross-branch action sequence
preferred outcome
rejected outcome
margin/success gap
```

This materialization should make the source relation explicit before any actor
or Gym integration.

## Source Inputs

Primary source run:

```text
runs/m1271_four_wheel_source_viability_calibration_smoke
```

Primary source corpus:

```text
runs/m1273_four_wheel_source_corpus_export/all_accepted_source_rows.csv
runs/m1273_four_wheel_source_corpus_export/near_boundary_source_rows.csv
runs/m1273_four_wheel_source_corpus_export/high_regret_source_rows.csv
runs/m1273_four_wheel_source_corpus_export/family_balanced_source_rows.csv
```

Subset counts:

```text
all accepted: 108
near_boundary: 19
high_regret: 32
near_boundary OR high_regret: 38
family_balanced: 63
```

Recommended first implementation materializes:

```text
primary subset: near_boundary OR high_regret
secondary subset: family_balanced
```

Reason:

```text
near_boundary rows are terminally useful;
high_regret rows are action-divergent;
family_balanced rows preserve source diversity.
```

## Intervention Semantics

For every accepted source pair, produce two branch-conditioned intervention
rows.

For condition A:

```text
preferred_candidate_id = best_candidate_A
rejected_candidate_id = best_candidate_B
preferred_margin = margin_A_best_A
rejected_margin = margin_A_best_B
preferred_success = best_A_success
rejected_success = A_using_B_success
margin_gap = margin_A_best_A - margin_A_best_B
```

For condition B:

```text
preferred_candidate_id = best_candidate_B
rejected_candidate_id = best_candidate_A
preferred_margin = margin_B_best_B
rejected_margin = margin_B_best_A
preferred_success = best_B_success
rejected_success = B_using_A_success
margin_gap = margin_B_best_B - margin_B_best_A
```

Accepted source rows guarantee:

```text
preferred_success == true
preferred_margin >= 0
best_action_l2 >= 0.12
cross_regret_A >= 0.02
cross_regret_B >= 0.02
```

The rejected action may be collision, horizon, or lower-margin success. Do not
discard rejected-success rows; margin-gap counterfactuals remain useful.

## Artifact Schema

M1277 should write:

```text
runs/m1277_four_wheel_source_intervention_materialization/summary.json
runs/m1277_four_wheel_source_intervention_materialization/intervention_rows.csv
runs/m1277_four_wheel_source_intervention_materialization/intervention_observations.csv
runs/m1277_four_wheel_source_intervention_materialization/intervention_action_sequences.csv
runs/m1277_four_wheel_source_intervention_materialization/source_pair_rows.csv
runs/m1277_four_wheel_source_intervention_materialization/materialization_limits.md
```

`intervention_rows.csv` fields:

```text
intervention_id
pair_id
source_subset
source_family
condition
fault_name
fault_family
scenario_id
seed
speed
obstacle_body_x
obstacle_body_y
obstacle_half_width
min_own_margin
min_cross_regret
near_boundary_margin_le_0_20
high_regret_ge_0_05
preferred_candidate_id
rejected_candidate_id
preferred_margin
rejected_margin
margin_gap
preferred_success
rejected_success
preferred_terminal_reason
rejected_terminal_reason
preferred_action_l2_from_shared_base
rejected_action_l2_from_shared_base
best_action_l2
```

`intervention_observations.csv` fields:

```text
intervention_id
obs_0 ... obs_71
```

The observation must be reconstructed from visible source state only:

```text
vx / vy / yaw_rate / actuator state / previous action / road geometry /
obstacle geometry
```

Forbidden observation fields:

```text
fault labels
per-wheel scales
per-wheel forces
candidate ids
success/collision/progress labels
preferred/rejected labels
search result fields
```

`intervention_action_sequences.csv` fields:

```text
intervention_id
role: preferred | rejected
candidate_id
step
steer
throttle
brake
```

`source_pair_rows.csv` should preserve one row per source pair used in the
materialization, with subset tags and source metrics.

## Materialization Counts

Expected counts for the first implementation:

```text
near_high_union source pairs: 38
near_high_union intervention rows: 76
family_balanced source pairs: 63
family_balanced intervention rows: 126
```

The implementation can export both subsets in one run by tagging
`source_subset`.

If a pair appears in both near-boundary and high-regret, do not duplicate it
within the `near_high_union` subset.

## Guardrails

M1277 must not:

```text
train;
run PPO;
promote;
use private holdout;
add fault/per-wheel metadata to actor observations;
lower accepted-source thresholds;
count source artifacts as driver performance;
claim self-identification;
claim high-fidelity validation.
```

Fault labels and branch labels may exist in source metadata columns of the
artifact, but they must not enter the `intervention_observations.csv` actor-view
columns.

## Acceptance Criteria

M1277 passes if:

```text
summary.json exists;
near_high_union source pair count equals 38;
near_high_union intervention row count equals 76;
family_balanced source pair count equals 63;
family_balanced intervention row count equals 126;
all observations have 72 finite values;
preferred_success is true for every intervention row;
preferred_margin >= 0 for every intervention row;
margin_gap >= 0.02 for every intervention row;
guardrails report false for training/PPO/promotion/private holdout/input change.
```

If those checks fail, M1277 must route to an audit or corpus repair instead of
actor/Gym integration.

## Next Step

Pre-register and run:

```text
experiments/manifests/m1277-paper-route-four-wheel-source-intervention-materialization.json
```
