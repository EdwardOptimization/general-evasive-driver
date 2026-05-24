# M636 Combined Source-7 Preserving Shape Implementation

## Purpose

M636 implements the combined no-training projected search designed in M635.

Question:

```text
Can a two-grid projected search keep source8/source0/source30 gains while
restoring source7?
```

Answer:

```text
Yes. All four focused sources have accepted candidates while preserving the
existing trust limits and thresholds.
```

## Implementation

New module:

```text
src/autodrift/combined_projected_sequence_shape.py
```

Focused tests:

```text
tests/test_combined_projected_sequence_shape.py
```

The runner executes two named grids and merges their artifacts:

```text
source8_recovery_grid
source7_preservation_grid
```

This keeps interpretation cleaner than a single large Cartesian grid.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.combined_projected_sequence_shape \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --source-table runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv \
  --baseline-source-summary runs/m633_targeted_source8_projected_shape/source_recovery_summary.csv \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --run-dir runs/m636_combined_source7_preserving_shape
```

Artifacts:

```text
runs/m636_combined_source7_preserving_shape/combined_projected_candidates.csv
runs/m636_combined_source7_preserving_shape/accepted_combined_sequences.csv
runs/m636_combined_source7_preserving_shape/source_recovery_summary.csv
runs/m636_combined_source7_preserving_shape/summary.json
```

## Results

Summary:

| Metric | Value |
| --- | ---: |
| candidate rollouts | `7884` |
| accepted combined candidates | `1424` |
| source8 recovered | `true` |
| source0 recovered | `true` |
| source7 recovered | `true` |
| source30 preserved | `true` |
| all four sources have acceptance | `true` |
| trust limits preserved | `true` |

Accepted candidates by source:

| Source | Accepted candidates |
| ---: | ---: |
| `8` | `664` |
| `30` | `430` |
| `0` | `196` |
| `7` | `134` |

Accepted candidates by grid:

| Grid | Accepted candidates |
| --- | ---: |
| source8_recovery_grid | `1290` |
| source7_preservation_grid | `134` |

Accepted targets:

| Target | Accepted candidates |
| --- | ---: |
| future_braking_deceleration | `760` |
| future_yaw_response | `664` |

Trust-limit maxima over the full candidate table:

```text
max sequence_mean_l2: 0.0799999966
max sequence_max_l2: 0.0999999940
max max_delta_delta_l2: 0.0225000083
```

## Source-Level Summary

| Source | Grid | Accepted | Best improvement | Best family | K | Status |
| ---: | --- | ---: | ---: | --- | ---: | --- |
| `7` | source7_preservation_grid | `134` | `0.025043` | targeted_decay_hold | `9` | recovered |
| `30` | source8_recovery_grid | `430` | `0.029507` | targeted_constant_delta | `9` | preserved |
| `8` | source8_recovery_grid | `664` | `0.026789` | targeted_constant_delta | `9` | recovered |
| `0` | source8_recovery_grid | `196` | `0.022995` | targeted_steer_build_brake_hold | `9` | recovered |

The source7 preservation grid resolves the M633 regression:

```text
M633 source7 accepted: 0
M636 source7 accepted: 134
M636 source7 best improvement: 0.025043
```

## Interpretation

M636 is the strongest positive diagnostic in this sequence-target branch:

```text
all four focused sources accepted
fresh and OOD surfaces represented
future_yaw_response and future_braking_deceleration represented
trust limits preserved
no training or PPO
```

It is still not automatic optimizer admission. The evidence is four focused
source rows from an increasingly tuned candidate-shape process. M637 must audit
whether this is broad enough to become a target corpus, or whether another
source-diversity expansion is required first.

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

## Decision

Decision:

```text
combined_source7_preserving_shape_implementation_pass_admit_audit
```

Blocked pending M637:

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
m637-combined-source7-preserving-shape-audit
```
