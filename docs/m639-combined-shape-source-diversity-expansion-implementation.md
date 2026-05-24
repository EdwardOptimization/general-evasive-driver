# M639 Combined Shape Source-Diversity Expansion Implementation

## Purpose

M639 implements and runs the no-training broad source-diversity expansion
designed in M638.

Question:

```text
Does the M636 combined projected-shape method still work when expanded from
four focused source rows to the broader M627 trust-primary non-collision source
set?
```

Answer:

```text
Yes. M639 passes the pre-registered source-diversity admission-candidate gate.
```

This remains diagnostic-only:

```text
no training
no PPO
no checkpoint promotion
no optimizer admission
no trust-region relaxation
no target-threshold relaxation
```

## Implementation

Added:

```text
src/autodrift/combined_shape_source_diversity_expansion.py
tests/test_combined_shape_source_diversity_expansion.py
```

The runner:

1. Loads M627 near-miss source rows.
2. Selects trust-primary non-collision rows.
3. Runs two M636-derived projected grid styles over the selected source set.
4. Writes candidate, accepted, source-recovery, and source-diversity artifacts.

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.combined_shape_source_diversity_expansion \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --source-table runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv \
  --near-miss-sources runs/m627_near_miss_trust_geometry/near_miss_sources.csv \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --run-dir runs/m639_combined_shape_source_diversity_expansion
```

## Artifacts

```text
runs/m639_combined_shape_source_diversity_expansion/summary.json
runs/m639_combined_shape_source_diversity_expansion/selected_expanded_source_rows.csv
runs/m639_combined_shape_source_diversity_expansion/expanded_projected_candidates.csv
runs/m639_combined_shape_source_diversity_expansion/accepted_expanded_sequences.csv
runs/m639_combined_shape_source_diversity_expansion/source_recovery_summary.csv
runs/m639_combined_shape_source_diversity_expansion/source_diversity_summary.csv
```

## Result

Summary:

```text
selected_source_rows: 9
selected_source_ids: 13, 14, 20, 32, 5, 30, 7, 0, 8
candidate_rollouts: 25596
accepted_expanded_candidates: 9885
accepted_source_rows: 9
accepted_unique_physical_pairs: 8
accepted_unique_left_seeds: 6
accepted_surfaces: 2
accepted_targets: 3
accepted_variants: 2
trust_limits_preserved: true
target_corpus_admission_candidate: true
```

Source-diversity summary:

| Set | Rows | Physical pairs | Left seeds | Surfaces | Variants | Targets | Max pair dominance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| selected_sources | 9 | 8 | 6 | 2 | 2 | 3 | 0.222222 |
| accepted_sources | 9 | 8 | 6 | 2 | 2 | 3 | 0.222222 |

Accepted counts by source:

| Source | Accepted |
| ---: | ---: |
| `13` | `2123` |
| `14` | `2123` |
| `20` | `1532` |
| `32` | `1532` |
| `5` | `1062` |
| `8` | `664` |
| `30` | `515` |
| `0` | `200` |
| `7` | `134` |

Accepted counts by grid:

```text
source8_recovery_style: 8042
source7_preservation_style: 1843
```

Accepted target coverage:

```text
future_yaw_response
future_lateral_accel_response
future_braking_deceleration
```

Trust-region maxima:

```text
sequence_mean_l2 max: 0.0799999998675452
sequence_max_l2 max: 0.0999999940395358
max_delta_delta_l2 max: 0.0225000083446502
```

## Interpretation

This is the first sequence-target result in this branch that passes the
pre-registered source-diversity admission-candidate criteria:

```text
accepted_source_rows >= 8
accepted_unique_physical_pairs >= 6
accepted_unique_left_seeds >= 6
accepted_surfaces >= 2
accepted_targets >= 2
trust_limits_preserved == true
```

It resolves the M637 concern that M636 was only a four-source diagnostic.

However, it does not directly admit training. The accepted candidate count is
large and unevenly distributed. Sources `13`, `14`, `20`, and `32` dominate raw
candidate count. A target corpus must be source-balanced and should cap rows per
source/grid/target before any actor update.

## Next Step

Admit:

```text
m640-source-diverse-sequence-target-corpus-design
```

M640 should design a corpus from M639 accepted sequences with:

```text
source-level caps
grid/target diversity
source-heldout split
weighting rules
no training yet
```

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
source_diverse_positive_diagnostic
```

Decision:

```text
combined_shape_source_diversity_expansion_pass_admit_corpus_design
```
