# M637 Combined Source-7 Preserving Shape Audit

## Purpose

M637 audits M636 before any target-corpus, actor-update, or source-expansion
decision.

Question:

```text
Is M636 broad enough for target-corpus admission?
```

Answer:

```text
No. M636 is the strongest positive diagnostic in this branch, but it is still
only four focused source rows. The next step should expand source diversity
using the combined projected shape method, not train yet.
```

## Evidence

M636 artifacts:

```text
runs/m636_combined_source7_preserving_shape/summary.json
runs/m636_combined_source7_preserving_shape/source_recovery_summary.csv
runs/m636_combined_source7_preserving_shape/accepted_combined_sequences.csv
docs/m636-combined-source7-preserving-shape-implementation.md
```

## Positive Result

M636 passes the focused-source objective:

| Source | Accepted candidates | Best improvement | Grid |
| ---: | ---: | ---: | --- |
| `8` | `664` | `0.026789` | source8_recovery_grid |
| `0` | `196` | `0.022995` | source8_recovery_grid |
| `7` | `134` | `0.025043` | source7_preservation_grid |
| `30` | `430` | `0.029507` | source8_recovery_grid |

Other checks:

```text
trust_limits_preserved: true
all_four_sources_have_acceptance: true
accepted targets: future_braking_deceleration and future_yaw_response
accepted surfaces: fresh and ood
training_used: false
ppo_used: false
promoted: false
```

This proves the candidate-shape direction is real:

```text
projection + local shape design can convert near misses into accepted source
rows under unchanged trust limits
```

## Why This Is Still Not Target-Corpus Ready

M636 accepted `1424` candidates, but candidate count is not source diversity.
The actual source-level breadth is:

```text
source rows: 4
unique physical pairs: 4
unique left seeds: 3
surfaces: 2
targets: 2
variants: 2
```

Earlier sequence-target audits treated `6` selected source rows and `5`
physical pairs as still too narrow. M636 is better mechanistically, but not
broader.

Training from this result would likely overfit the source-specific grids.

## Decision

Do not admit optimizer training.

Do not design an actor update yet.

Do not treat `1424` accepted candidates as independent examples.

Admit a no-training source-diversity expansion design:

```text
m638-combined-shape-source-diversity-expansion-design
```

M638 should apply the combined projected-shape method to a broader trust-primary
source set, not just the four focused rows.

Candidate source set:

```text
all M627 trust-primary non-collision near-miss sources
plus focused sentinel/recovery rows from M636
```

Suggested pass criteria for a later implementation:

```text
accepted source rows >= 8
unique physical pairs >= 6
unique left seeds >= 6
surfaces >= 2
targets >= 2
trust_limits_preserved == true
```

These are diagnostic criteria, not a training permission.

## Contract Checks

```text
diagnostic_only: true
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
target_acceptance_thresholds_changed: false
trust_regions_changed: false
```

## Final Classification

Classification:

```text
strong_positive_not_source_diverse
```

Decision:

```text
combined_source7_preserving_shape_audit_admit_source_diversity_expansion
```

Next branch:

```text
m638-combined-shape-source-diversity-expansion-design
```
