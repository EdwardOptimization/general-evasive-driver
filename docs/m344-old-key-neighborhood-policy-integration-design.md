# M344 Old-Key Neighborhood Policy Integration Design

M344 defines how the M341/M343 old-key neighborhood surface enters the
acceptance stack. This is a design-only milestone: no PPO, no actor update, no
checkpoint repair, no promotion, and no actor-input contract change.

## What M343 Proved

M343 formalized the M341 old-key neighborhood evidence:

```text
broad rows: 179
broad seed blocks: 5
broad max seed-block dominance: 0.234637

compact rows: 40
compact seed blocks: 5
compact max seed-block dominance: 0.25
compact max physical-pair dominance: 0.025

selected-alpha accepted regressions: 0
compact selected gap p10: -0.0000181822
compact selected gap min: -0.0000489009

repaired-endpoint accepted regressions: 15
compact endpoint gap p10: -0.0040711523
compact endpoint gap min: -0.0506599075

M133 / 9944 diagnostic visible: true
```

This is enough to stop treating one historical old-key row as the only
available old-key proof signal.

## Important Limitation

The M342/M343 gate currently evaluates saved M341 columns:

```text
selected_*
endpoint_*
```

That is correct for the M335 alpha versus M335 repaired endpoint audit, but it
is not yet a replayable gate for an arbitrary future PPO candidate.

Therefore the policy has two stages:

```text
M343:
  proves the source-diverse old-key neighborhood surface is valid

M345:
  must implement or formalize candidate replay on that surface before future
  PPO candidates can use it as a first-class acceptance gate
```

Do not use the static M343 result as if it automatically certifies future
checkpoints.

## New Old-Key Gate Meaning

The old-key neighborhood gate should become the first-class old-key proof gate
once a candidate replay adapter exists.

For a future candidate, the gate should report:

```text
candidate accepted regressions
candidate gap p10
candidate gap min
candidate normal-margin delta
candidate wrong-history margin delta
source-diversity metrics
M133 / 9944 diagnostic visibility
```

The candidate should pass the distributional old-key gate only if:

```text
accepted regressions == 0
gap p10 >= -0.0005
gap min >= -0.002
broad diversity targets pass
compact diversity targets pass
M133 / 9944 diagnostic is visible
```

The repaired-endpoint repair-needed thresholds remain useful as regression-test
evidence for the gate implementation:

```text
accepted regressions >= 2
or gap p10 <= -0.001
or gap min <= -0.01
```

They are not a promotion criterion. They only verify that the gate still catches
the known bad endpoint.

## Singleton 9944 Policy

The historical row `9944|perturbed|28|28` is not removed.

It remains:

```text
historical continuity diagnostic
single-row warning signal
reported artifact in gate and promotion docs
reason to inspect candidate behavior manually when it conflicts with the
distributional gate
```

It no longer remains:

```text
the only old-key gate
a standalone PPO-continuation veto when the source-diverse old-key neighborhood
gate passes
```

Use this classification when the neighborhood gate passes but the singleton
row warns:

```text
single_key_gap_floor_warning
```

This warning may advance to first replay or full public gate, but it must be
reported. It cannot by itself promote a checkpoint.

Use hard failure when any of the following occurs:

```text
old-key neighborhood gate fails
M133 / 9944 diagnostic is missing
compact or broad diversity target fails
candidate accepted regressions > 0 on the compact old-key surface
candidate gap p10 or min violates threshold
actor input contract changes
private holdout is used for repair
```

Recommended failure taxonomy:

| Situation | Classification |
| --- | --- |
| Compact/broad diversity fails | `lineage_invalid` |
| Candidate old-key surface regresses | `protected_key_window_failure` |
| Singleton 9944 warns but neighborhood passes | `single_key_gap_floor_warning` in docs; no process-v2 failure type |
| 9944 diagnostic hidden or missing | `lineage_invalid` |
| Gate metric looks good but replay surface fails | `metric_artifact` or `proof_washout` depending on evidence |

## Acceptance Stack

For the next PPO continuation family, use this order:

```text
0. Human-view actor-input contract check.
1. Exact M297 rejected-history preference no-regression.
2. Exact M270 source-balanced outcome no-regression.
3. Source-diverse protected replay bundle.
4. Old-key neighborhood replay gate.
5. M133 / 9944 diagnostic report and classification.
6. First replay gates.
7. Full six replay gates.
8. Behavior seeds 9505 and 9506.
9. Research review, scoreboard, status, and validation.
10. Promotion decision.
```

The old-key neighborhood gate is a proof-retention gate, not a replacement for
full replay or behavior gates.

## Promotion Rule

A candidate cannot be promoted from the old-key neighborhood gate alone.

Promotion requires:

```text
exact M297 and M270 no-regression
source-diverse protected bundle pass
old-key neighborhood replay gate pass
M133 / 9944 diagnostic visible
all six replay gates pass
behavior seeds retain success / termination behavior
no actor-input or env-contract change
no private-holdout tuning
```

If the old-key neighborhood gate passes but singleton `9944` warns, promotion is
allowed only if the final promotion milestone explicitly reports:

```text
single_key_gap_floor_warning
why it is singleton-local rather than distributional old-proof erosion
all distributional old-key metrics
all replay and behavior gates
```

If the old-key neighborhood gate fails, the candidate is rejected or repaired
before first replay or promotion.

## Next Implementation Need

M345 should implement the replayable candidate layer for this policy.

The minimum acceptable M345 output is:

```text
candidate replay rows for the M341 compact corpus
comparison summary for base versus candidate
candidate metrics compatible with the M342/M343 thresholds
M335 alpha reproduced as pass
M335 repaired endpoint reproduced as fail / repair-needed
focused tests for replayable schema and threshold logic
```

M345 should not run PPO. It should make the old-key neighborhood gate usable for
future arbitrary checkpoints.

## Decision

M344 defines the policy and admits the required implementation step.

Decision:

```text
admit_m345_old_key_neighborhood_replay_gate_adapter
```
