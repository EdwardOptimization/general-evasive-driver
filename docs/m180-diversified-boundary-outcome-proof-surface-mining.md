# M180 Diversified Boundary Outcome Proof Surface Mining

M179 found a local boundary-relocated wrong-history success-drop surface, but the
robustness gate rejected it as duplicate-dominated: strict deduplication left
only `3` physical pairs and `2` left steps.

M180 tests whether simple obstacle geometry diversification can broaden that
surface before any objective construction or PPO.

Result: negative. Lateral offsets and longitudinal offsets increase the number
of replay rows and slightly increase reset/zero-current accepted rows, but they
do not improve strict wrong-history diversity. The accepted wrong-history rows
remain dominated by the same `3` physical pairs and `2` left steps.

## Lateral Offset Sweep

Run:

```text
runs/m180_lateral_offset_boundary_surface_seed9510
```

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy m168_strict=runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --checkpoint-policy m170_split=runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --outcome-csv runs/m178_dual_checkpoint_outcome_proof_surface_seed9510/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-pairs-per-checkpoint-target 0 \
  --min-base-action-distance 0.02 \
  --target-normal-margins 0.005,0.01,0.02,0.05,0.10,0.15 \
  --half-width-inflations 0 \
  --body-lateral-offsets=-0.50,-0.25,0.0,0.25,0.50 \
  --min-margin-gap 0.02 \
  --min-accepted-wrong-rows 40 \
  --report-variants wrong_matched_history,reset_hidden,zero_current_response,zero_action_history,delayed_history \
  --device cpu \
  --run-dir runs/m180_lateral_offset_boundary_surface_seed9510
```

Result:

| Metric | M179 source-only | M180 lateral offsets |
| --- | ---: | ---: |
| candidate rows | 658 | 658 |
| replay rows | 16880 | 84400 |
| accepted wrong-history rows | 48 | 48 |
| accepted wrong-history source pairs | 20 | 20 |
| wrong-history success drops | 48 | 48 |
| accepted reset rows | 1448 | 1506 |
| accepted zero-current rows | 704 | 764 |

Robustness:

```text
runs/m180_lateral_offset_robustness_seed9510
```

| Gate | Observed | Threshold | Passed |
| --- | ---: | ---: | --- |
| accepted wrong rows | 48 | 40 | true |
| accepted wrong physical pairs | 3 | 10 | false |
| accepted wrong left steps | 2 | 5 | false |
| accepted wrong checkpoints | 2 | 2 | true |
| accepted wrong targets | 1 | 1 | true |
| accepted wrong normal-margin buckets | 2 | 2 | true |
| success-drop fraction | 1.000000 | 1.000000 | true |
| max rows per physical pair fraction | 0.333333 | 0.250000 | false |

Decision:

```text
reject_duplicate_dominated_boundary_surface
```

## Longitudinal Offset Sweep

Run:

```text
runs/m180_longitudinal_offset_boundary_surface_seed9510
```

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy m168_strict=runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --checkpoint-policy m170_split=runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --outcome-csv runs/m178_dual_checkpoint_outcome_proof_surface_seed9510/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-pairs-per-checkpoint-target 0 \
  --min-base-action-distance 0.02 \
  --target-normal-margins 0.005,0.01,0.02,0.05,0.10,0.15 \
  --half-width-inflations 0 \
  --body-longitudinal-offsets=-2.0,-1.0,0.0,1.0,2.0 \
  --min-margin-gap 0.02 \
  --min-accepted-wrong-rows 40 \
  --report-variants wrong_matched_history,reset_hidden,zero_current_response,zero_action_history,delayed_history \
  --device cpu \
  --run-dir runs/m180_longitudinal_offset_boundary_surface_seed9510
```

Result:

| Metric | M179 source-only | M180 longitudinal offsets |
| --- | ---: | ---: |
| candidate rows | 658 | 658 |
| replay rows | 16880 | 84050 |
| accepted wrong-history rows | 48 | 56 |
| accepted wrong-history source pairs | 20 | 20 |
| wrong-history success drops | 48 | 56 |
| accepted reset rows | 1448 | 1594 |
| accepted zero-current rows | 704 | 1062 |

Robustness:

```text
runs/m180_longitudinal_offset_robustness_seed9510
```

| Gate | Observed | Threshold | Passed |
| --- | ---: | ---: | --- |
| accepted wrong rows | 56 | 40 | true |
| accepted wrong physical pairs | 3 | 10 | false |
| accepted wrong left steps | 2 | 5 | false |
| accepted wrong checkpoints | 2 | 2 | true |
| accepted wrong targets | 1 | 1 | true |
| accepted wrong normal-margin buckets | 2 | 2 | true |
| success-drop fraction | 1.000000 | 1.000000 | true |
| max rows per physical pair fraction | 0.428571 | 0.250000 | false |

Decision:

```text
reject_duplicate_dominated_boundary_surface
```

## Dominating Pairs

The accepted rows remain concentrated in the same strict physical pairs:

```text
(9530, 18, 9540, 21)
(9530, 18, 9540, 24)
(9530, 21, 9540, 24)
```

Lateral offsets add no new accepted wrong-history rows. Longitudinal offsets add
8 rows, but still from the same strict physical pair set.

## Interpretation

What M180 supports:

- M179's duplicate domination is not solved by simple lateral obstacle offsets.
- Longitudinal offsets slightly increase row count but worsen pair domination.
- Reset-hidden and zero-current-response outcome sensitivity is much broader
  than matched wrong-history sensitivity.

What M180 does not support:

- no diversified wrong-history proof surface;
- no objective/corpus/PPO admission;
- no basis to select M170 over M168.

## Decision

Complete M180 as a negative diversification result. Do not continue blind
geometry sweeps.

The next step should change the mining strategy: lower or remove the
base-action-distance filter and explicitly search for source-pair diversity
before running expensive multi-variant sweeps.
