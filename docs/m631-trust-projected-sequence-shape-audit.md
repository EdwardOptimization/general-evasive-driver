# M631 Trust-Projected Sequence Shape Audit

## Purpose

M631 audits the M630 projected sequence result before any optimizer or next
candidate-shape branch.

Question:

```text
Is M630 strong enough for optimizer admission, or should the next step remain
no-training candidate-shape research?
```

Answer:

```text
M630 is a narrow positive diagnostic, not optimizer-ready. Projection preserves
trust limits and recovers source 30, but accepted evidence remains source-narrow.
The next no-training branch should target source 8, which is close to the margin
threshold after projection.
```

## Evidence

M630 artifacts:

```text
runs/m630_trust_projected_sequence_shape/summary.json
runs/m630_trust_projected_sequence_shape/projected_sequence_candidates.csv
runs/m630_trust_projected_sequence_shape/source_recovery_summary.csv
docs/m630-trust-projected-sequence-shape-implementation.md
```

## Gate Checks

| Gate | Result |
| --- | --- |
| trust limits preserved | pass |
| training used | no |
| PPO used | no |
| checkpoint promoted | no |
| optimizer admission | no |
| target thresholds changed | no |
| trust regions changed | no |

M630 correctly preserved:

```text
max sequence_mean_l2: 0.0799999997 <= 0.08
max sequence_max_l2: 0.0999999881 <= 0.10
max max_delta_delta_l2: 0.0799999982 <= 0.08
```

## Result Classification

Summary:

| Metric | Value |
| --- | ---: |
| focused source rows | `4` |
| candidate rollouts | `7596` |
| accepted projected candidates | `9` |
| accepted physical pairs | `2` |
| accepted left seeds | `2` |
| accepted targets | `1` |
| recovered zero-accepted sources | `1` |

Source recovery:

| Source | Before | After | Best improvement | Status |
| ---: | ---: | ---: | ---: | --- |
| `30` | `0` | `4` | `0.021397` | recovered |
| `7` | `3` | `5` | `0.020817` | improved but already accepted |
| `8` | `0` | `0` | `0.018752` | near miss |
| `0` | `0` | `0` | `0.015290` | still below threshold |

Classification:

```text
diagnostic-positive for projected trust feasibility
diagnostic-positive for recovering one zero-accepted source
diagnostic-negative for optimizer-admission diversity
```

## Why This Is Not Optimizer-Ready

M630 accepted candidates are only:

```text
source 7: 5 candidates
source 30: 4 candidates
```

This is not enough source-level evidence for a supervised target corpus or
actor update. It still covers only `2` physical pairs and `1` target. Training
from this would likely overfit another narrow surface.

Do not promote, train, or run PPO from M630.

## Next Branch

The most useful next row is source `8`:

```text
source: 8
tier: core_boundary
surface: ood
target: future_yaw_response
variant: delayed_history
accepted_before_m624: 0
best_projected_margin_improvement: 0.018752
margin gap to threshold: 0.001248
```

This is close enough that a targeted local shape design is more justified than
immediately returning to broad source re-mining. Source `0` remains farther
below threshold and should be secondary.

M632 should be design-only and should not lower the margin threshold. It should
define a source-8 targeted candidate-shape search using:

```text
existing trust limits
same margin/risk thresholds
local perturbations around source-8 best projected signs
possibly K=7/K9 smooth schedules
source-level recovery as the main metric
```

Collision-primary sources remain a separate branch.

## Decision

Decision:

```text
trust_projected_sequence_shape_audit_admit_source8_shape_design
```

Blocked:

```text
optimizer admission
actor training
PPO
checkpoint promotion
trust-region widening
target-threshold lowering
```

Next branch:

```text
m632-targeted-source8-projected-shape-design
```
