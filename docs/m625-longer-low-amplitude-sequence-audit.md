# M625 Longer Low-Amplitude Sequence Audit

## Purpose

M625 audits the M624 K=7 low-amplitude diagnostic.

Question:

```text
Did K=7 solve the accepted source-diversity blocker?
```

Answer:

```text
No. It strengthened candidate-level signal on existing accepted sources, but
did not add source-level accepted breadth.
```

## Evidence

M624 artifacts:

```text
runs/m624_longer_low_amplitude_sequence_miner/summary.json
runs/m624_longer_low_amplitude_sequence_miner/accepted_candidate_sequences.csv
runs/m624_longer_low_amplitude_sequence_miner/accepted_sequences.csv
runs/m624_longer_low_amplitude_sequence_miner/unaccepted_rows.csv
runs/m624_longer_low_amplitude_sequence_miner/sequence_candidates.csv
```

## M624 vs M621

| Metric | M621 | M624 |
| --- | ---: | ---: |
| candidate rollouts | `10440` | `22140` |
| accepted candidates | `189` | `607` |
| selected accepted sequences | `6` | `6` |
| selected physical pairs | `5` | `5` |
| selected left seeds | `4` | `4` |
| accepted candidate physical pairs | `5` | `5` |
| accepted candidate left seeds | `4` | `4` |
| selected margin improvement mean | `0.056784` | `0.068523` |
| selected margin improvement max | `0.093048` | `0.121356` |

M624 improves candidate count and margin on already accepted rows, but it does
not improve source-level diversity.

## Classification

Classification:

```text
diagnostic-positive for longer-prefix utility
diagnostic-negative for source-diversity recovery
```

Do not train from this result.

Do not treat the `607` accepted candidates as independent source examples:

```text
accepted candidate physical pairs: 5
accepted candidate left seeds: 4
```

## Near-Miss Pattern

Top unaccepted rows show a consistent pattern:

| Source | Tier | Best Improvement | Rejection |
| ---: | --- | ---: | --- |
| `30` | support_boundary | `0.030757` | outside_sequence_trust_region |
| `1` | core_boundary | `0.025914` | outside_sequence_trust_region |
| `0` | support_boundary | `0.023657` | outside_sequence_trust_region |
| `8` | core_boundary | `0.022960` | outside_sequence_trust_region |
| `2` | core_boundary | `0.021347` | outside_sequence_trust_region |
| `15` | core_boundary | `0.021143` | candidate_collision |
| `21` | core_boundary | `0.020580` | outside_sequence_trust_region |

Rows at or above the `0.02` margin threshold:

```text
outside_sequence_trust_region: 6
candidate_collision: 1
```

Candidate-level view:

```text
trust-blocked candidates with margin_improvement >= 0.02: 775
unique source rows among those candidates: 13
```

This suggests the next useful diagnostic is not more brute-force candidate
count. It is trust-geometry analysis.

## Decision

Decision:

```text
longer_low_amplitude_sequence_audit_admit_trust_geometry_design
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
m626-near-miss-trust-geometry-design
```

M626 should design a no-training analyzer that classifies near-miss candidates
by which trust constraint fails:

```text
sequence_mean_l2 > 0.08
sequence_max_l2 > 0.10
max_delta_delta_l2 > 0.08
candidate_collision
off-road / spin-out
```

It should also identify whether near-miss candidates could be made feasible by
candidate-shape design while preserving the same trust limits, rather than by
relaxing limits.

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
