# M644 Source-Balanced BC-v2 Objective Implementation

## Purpose

M644 implements the exact no-update BC-v2 objective evaluator designed in M643.
It loads the M641 source-balanced sequence corpus and the BC5660 checkpoint,
then computes normal-hidden and variant-hidden first-action losses plus
source-balanced sequence-delta metrics.

No optimizer, training loop, PPO, checkpoint write, actor update, or promotion
occurs.

## Command

```bash
PYTHONPATH=src python -m autodrift.source_balanced_bc_v2_objective \
  --corpus runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz \
  --metadata runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --run-dir runs/m644_source_balanced_bc_v2_objective
```

## Artifacts

- `runs/m644_source_balanced_bc_v2_objective/summary.json`
- `runs/m644_source_balanced_bc_v2_objective/row_bc_v2_metrics.csv`
- `runs/m644_source_balanced_bc_v2_objective/source_bc_v2_summary.csv`
- `runs/m644_source_balanced_bc_v2_objective/split_bc_v2_summary.csv`
- `runs/m644_source_balanced_bc_v2_objective/target_bc_v2_summary.csv`

## Result

```text
rows: 431
source_count: 9
observation_dim: 72
hidden_dim: 64
max_sequence_length: 9
first_action_normal_loss: 0.002101438195079985
first_action_variant_loss: 0.0025997091525714437
first_action_base_loss: 0.0021014375507382287
sequence_delta_target_mse: 0.00203998548446608
sequence_delta_mean_step_l2: 0.0773480846102788
first_action_gap_l2_mean: 0.010549428633947821
normal_action_to_base_l2_mean: 0.00000004042586998659383
variant_action_to_stored_l2_mean: 0.000000036475309204907504
train_loss: 0.0020440442793534784
source_holdout_validation_loss: 0.0022162260262924625
finite_metrics: true
actor_parameters_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

The model checksum is identical before and after evaluation:

```text
d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
```

Source weight balance remains valid:

```text
source_count: 9
expected_source_weight: 0.1111111111111111
max_abs_source_weight_error: 0.0000000008278422947149977
total_weight: 1.0000000060535967
source_weight_balanced: true
```

## Split Summary

| Split | Rows | Sources | Normal Loss | Variant Loss | Sequence Delta MSE | Gap L2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `train` | 271 | 6 | 0.0020440442793534784 | 0.0025504226844296073 | 0.002054882368650409 | 0.011238827126710857 |
| `source_holdout_validation` | 160 | 3 | 0.0022162260262924625 | 0.0026982820886485596 | 0.0020101917161598555 | 0.009170631651310981 |

## Target Summary

| Target | Rows | Sources | Normal Loss | Variant Loss | Sequence Delta MSE | Gap L2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `future_braking_deceleration` | 95 | 3 | 0.002203060538048117 | 0.002671335527690972 | 0.0021187091297119477 | 0.009062967116212179 |
| `future_lateral_accel_response` | 48 | 1 | 0.0024996011278664203 | 0.0033069764304520218 | 0.0021134772250603687 | 0.014231273195749034 |
| `future_yaw_response` | 288 | 5 | 0.001960832202997355 | 0.0024152798721037206 | 0.0019780529493976587 | 0.010704936628491155 |

## Interpretation

M644 passes the implementation gate. The evaluator is live and no-update:
normal-hidden first actions reconstruct the stored base first actions to within
`4.1e-8` weighted mean L2, and variant-hidden actions reconstruct the stored
variant base actions to within `3.7e-8`.

The first-action normal loss equals the base first-action loss, which confirms
that M641 targets are local corrections around current BC5660 behavior rather
than already-applied actor changes.

The variant loss is higher than normal loss overall, but the gap is modest
(`0.01055` weighted L2 mean). Source-level summaries show wrong-history rows
still have especially small normal/variant gaps: source `30` gap `0.000792`
and source `32` gap `0.000578`. This is consistent with the earlier M587/M588
negative finding that BC5660 has weak accumulated-history action sensitivity.

Therefore M644 admits a frozen-actor head-only smoke design. It does not admit
a direct actor update.

## Decision

`source_balanced_bc_v2_objective_implementation_pass_admit_head_only_design`

## Next

`m645-bc-v2-head-only-smoke-design`
