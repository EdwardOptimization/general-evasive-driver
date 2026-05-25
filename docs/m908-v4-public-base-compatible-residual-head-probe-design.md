# M908 V4 Public-Base Compatible Residual-Head Probe Design

## Purpose

M908 designs the safe route after M907:

```text
M399 public base actor feature_dim: 128
M761 residual head feature_dim: 64
```

M908 is design-only:

```text
no residual training in M908
no actor update
no exact execution
no replay
no PPO
no checkpoint promotion
no actor input change
```

## Design Principle

Do not adapt the M761 residual head into M399.

Instead, regenerate the residual head in the M399 feature basis:

```text
base actor: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
actor contract: P0 human-view no-wheel 72-dim frame
actor feature_dim: 128
trainable scope: residual head only
actor backbone: frozen
PPO: forbidden
promotion: forbidden
```

The new head should be an M399-compatible version of the M761-style diagnostic
residual probe, not a driver checkpoint.

## Existing Tooling

The existing M761 tool already trains a residual head from frozen recurrent
actor features:

```text
python -m autodrift.v4_sequence_objective_probe
```

M761 used:

```text
checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
feature_dim: 64
positive rows: runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv
contrast rows: runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv
scenario config: configs/extreme_fault_distribution_v4_scenarios.json
```

For M399, the same tool should produce:

```text
feature_dim: 128
residual parameter count: 8451
```

because the residual head architecture is:

```text
Linear(feature_dim, 64) -> Tanh -> Linear(64, 3)
```

## M909 Implementation Plan

M909 should run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_sequence_objective_probe \
  --checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --corpus-summary runs/m755_v4_sequence_outcome_corpus_export/summary.json \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --run-dir runs/m909_v4_public_base_residual_head_probe \
  --device cpu \
  --epochs 40 \
  --seed 9090
```

M909 may train only the residual head. The M399 actor must remain frozen.

Required M909 artifacts:

```text
runs/m909_v4_public_base_residual_head_probe/summary.json
runs/m909_v4_public_base_residual_head_probe/residual_head.pt
runs/m909_v4_public_base_residual_head_probe/alpha_metrics.csv
runs/m909_v4_public_base_residual_head_probe/objective_rows.csv
runs/m909_v4_public_base_residual_head_probe/training_metrics.csv
runs/m909_v4_public_base_residual_head_probe/rejected_rows.csv
```

## M909 Acceptance Gates

M909 may be considered a residual-head compatibility positive only if:

```text
checkpoint == runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
actor_backbone_changed == false
residual_only_training == true
ppo_used == false
promoted == false
checkpoint_promoted == false
metadata_missing_rows == 0
sample_reconstruction_success_rate >= 0.98
residual_head_pt exists
residual_head.feature_dim == 128
residual_parameter_count == 8451
candidate_alpha_count >= 1
```

If `candidate_alpha_count == 0`, M909 is still useful diagnostic evidence, but
public-base pair-delta integration should stay blocked and route to
public-base target regeneration or residual-free objective sanity.

## After M909

M909 does not itself prove pair-delta objective compatibility.

If M909 passes, the next milestone should be an exact no-update compatibility
audit that replaces the M761 residual head in M906 with:

```text
runs/m909_v4_public_base_residual_head_probe/residual_head.pt
```

That later audit must use the enriched M880 pair-delta rows:

```text
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_train_public_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_eval_public_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_source_holdout_public_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_new_signature_holdout_public_rows.csv
```

and must require:

```text
tensor_rows_reconstructed == 247
missing_tensor_count == 0
exact_losses_finite == true
actor_parameters_changed == false
training_started == false
optimizer_started == false
ppo_used == false
promoted == false
```

Only after that exact no-update audit passes can a public-base objective-only
actor-coupling probe be designed.

## Target-Lineage Safeguards

The M880 action targets were created in the M568/M761 diagnostic branch. M908
therefore does not claim they transfer to M399.

The safe sequence is:

```text
1. M909: build M399-compatible residual head from M399 features.
2. M910: exact no-update M880 compatibility using M399 + M909 head.
3. Later: if exact compatibility passes, design a tiny public-base
   objective-only actor-coupling probe with exact holdout gates.
```

The M568/M761 branch remains diagnostic lineage only. M568-rooted raw
candidates must not be compared against M399 as promoted public-base
improvements.

## Rejected Shortcuts

Rejected:

```text
pad M761 residual features from 64 to 128;
truncate M399 features from 128 to 64;
learn a 128-to-64 adapter without a registered objective and gates;
change actor observations;
run replay before exact no-update compatibility;
run PPO before objective-only public-base evidence;
promote residual-head or M568-rooted candidates.
```

## Supported Claims

M908 supports:

```text
1. Public-base integration has a safe next implementation route.
2. The route uses M399's own 128-dim feature basis.
3. The route preserves the P0 human-view actor contract.
4. Replay, PPO, actor update, and promotion remain blocked until exact
   compatibility evidence exists.
```

## Unsupported Claims

M908 does not support:

```text
M399 residual-head training success;
M880 pair-delta exact compatibility;
public-base objective update feasibility;
replay retention;
generalization improvement;
PPO safety;
checkpoint promotion.
```

## Decision

Decision:

```text
public_base_128dim_residual_head_probe_design_admit_m909
```

Next:

```text
m909-v4-public-base-residual-head-probe-implementation
```

M909 may train a residual head only. It must freeze the M399 actor and keep
replay, PPO, actor update, and promotion blocked.
