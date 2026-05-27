# M1100 V4 Public Base Family-Aggregate Cross-Family Replay Audit

## Purpose

M1100 audits the M1099 cross-family replay report before any objective
optimization.

This milestone does not train, run PPO, run replay, run objective optimization,
mine rows, promote a checkpoint, use private holdout, or change actor inputs.

## Inputs

```text
runs/m1099_family_aggregate_replay_sanity/summary.json
runs/m1099_family_aggregate_replay_sanity/cross_family_policy_summary.csv
runs/m1099_family_aggregate_replay_sanity/cross_family_replay_rows.csv
runs/m1099_family_aggregate_replay_sanity/failed_duplicate_geometry_groups.csv
```

## Source-Policy Proof

M1099 source-policy replay remains valid:

```text
source rows: 146
source-policy replay rows: 146
normal successes: 146
wrong-history successes: 0
success drops: 146
physical pairs: 18
source checkpoints: 4
targets: 3
gate pass: true
```

This means the family-aggregate export preserves its intended proof relation
when each row is evaluated by its own source policy.

## Cross-Family Failures

Cross-family replay is a report, not a source-policy veto:

```text
cross-family replay rows: 584
failed replay rows: 23
family rows with any cross-family failure: 13
family rows passing all 4 policies: 133
```

The all-policy intersection remains broad enough for a replay-calibrated route:

```text
rows: 133
physical pairs: 14
source labels: 4
targets: 3
left steps: 9
duplicate geometry groups: 68

target distribution:
  future_yaw_response: 79
  future_braking_deceleration: 49
  future_lateral_accel_response: 5

source distribution:
  proof_current: 39
  short61049: 27
  short61050: 18
  short61051: 49
```

## Failure Classes

### Source-Specific Normal-History Failures

Rows `140..145` are `short61050` braking rows. They pass under their source
policy but fail normal-history success under `proof_current` and `short61049`.

This is not evidence that the source-policy export is invalid. It means those
rows are source-specific braking boundary rows and should not be mixed into an
aggregate objective unless the objective first applies family-intersection
filtering.

### Wrong-History Becomes Safe Under Another Policy

Rows `72`, `139`, `135..138`, and `30` keep normal-history success but lose the
wrong-history failure relation under at least one non-source policy. The wrong
history margins are small positive values near the boundary, so the issue is
cross-family sensitivity rather than a gross replay or metadata error.

These rows are useful diagnostics, but they are not safe aggregate objective
rows without additional filtering.

### Duplicate Geometry Concentration

The failed duplicate geometry groups are concentrated in a few families:

```text
g00068: 4 rows, short61051 yaw, wrong-history safe under proof_current
g00001..g00003: 6 rows, short61050 braking, normal-history fail under proof_current/short61049
g00061/g00067: short61049 yaw, wrong-history safe under several policies
g00051: 1 short61051 braking row, wrong-history safe under short61050
```

This supports a replay-calibrated selector instead of a direct aggregate
objective.

## Route Decision

The next safe route is:

```text
family-intersection replay-calibrated rows
```

Reasons:

1. Source-policy proof passes for all `146` rows, so the export itself is valid.
2. Direct mixed-source objective optimization is not defensible because 13 rows
   do not preserve the proof relation across the public-base family.
3. The all-policy intersection still has `133` rows, `14` physical pairs, `4`
   source labels, `3` targets, and `9` left steps, which is enough to design a
   deterministic selector without weakening thresholds.
4. Source-specific corpora are a fallback, not the first route, because the
   intersection is not sparse.
5. Target-base hidden-state rebuild is not yet justified; the observed failures
   are explained by source-specific closed-loop policy behavior.

## Decision

```text
family_aggregate_cross_family_audit_route_to_intersection_selector_design
```

Next:

```text
m1101-v4-public-base-family-aggregate-intersection-selector-design
```

M1101 should design a deterministic selector over the existing M1099 replay
artifacts. It should keep rows only when every public-base family policy
preserves normal-history success and wrong-history failure, preserve all
source/duplicate metadata, and fail closed if source or target diversity becomes
sparse.

## Validation

Research validation:

```text
make research-validate
```

Result:

```text
research validation passed
```
