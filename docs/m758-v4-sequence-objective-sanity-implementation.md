# M758 V4 Sequence Objective Sanity Implementation

## Purpose

M758 implements the no-training exact/offline sanity evaluator designed in M757.

The question is:

```text
Can the M755 v4 sequence corpus be reconstructed into exact objective samples
with finite normal-retention and intervention-gap metrics before any actor
update?
```

This milestone performs no training:

```text
no actor update
no optimizer step
no PPO
no checkpoint promotion
no actor-input change
```

The checkpoint is loaded only for deterministic replay/evaluation.

## Implementation

Added:

```text
src/autodrift/v4_sequence_objective_sanity.py
tests/test_v4_sequence_objective_sanity.py
```

The evaluator:

```text
1. reads M755 positive and contrast rows;
2. reconstructs seed/fault/step source snapshots with the v4 scenario config;
3. replays normal and outcome-critical intervention variants using the frozen
   checkpoint;
4. compares replayed first actions with the exported M755 base actions;
5. computes normal anchor, intervention anchor, gap preservation, target gap,
   gap deficit, and optional hard-negative calibration metrics;
6. writes objective_rows.csv, objective_metrics.csv, rejected_rows.csv, and
   summary.json.
```

Focused tests verify:

```text
metadata artifacts classify before reconstruction status;
reconstruction failures are classified explicitly;
hard-negative sparsity is separate from exact metric validity;
metric summaries report overall and stratified values.
```

## Registered Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v4_sequence_objective_sanity \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --corpus-summary runs/m755_v4_sequence_outcome_corpus_export/summary.json \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --fault-config configs/extreme_fault_distribution_v4_scenarios.json \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --run-dir runs/m758_v4_sequence_objective_sanity \
  --device cpu
```

## Smoke

A 32-row smoke reconstructed all samples:

```text
positive_rows: 32
reconstructed_rows: 32
sample_reconstruction_success_rate: 1.0
normal_intervention_gap_mean: 0.027384
hard_negative_available_fraction: 1.0
result_class: v4_sequence_objective_sanity_pass
actor_parameters_changed: false
```

The smoke only checked runtime/schema. The full registered run is the evidence.

## Result

Run directory:

```text
runs/m758_v4_sequence_objective_sanity
```

Summary:

```text
result_class: v4_sequence_objective_hard_negative_sparse

positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
metadata_missing_rows: 0
duplicate_group_ids: 0
missing_normal_rows: 0
missing_source_snapshots: 0
rejected_rows: 0
normal_group_count: 1213

normal_anchor_mse_mean: 0.0
intervention_anchor_mse_mean: 0.0
normal_intervention_gap_mean: 0.024908
normal_intervention_gap_p10: 0.021141
target_gap_mean: 0.041716
gap_deficit_mean: 0.016809
gap_deficit_p95: 0.021590

hard_negative_available_fraction: 0.721352
hard_negative_sparse: true
claim_boundary_levels:
  current_model_or_proxy

training_started: false
optimizer_started: false
checkpoint_loaded_for_eval_only: true
ppo_used: false
promoted: false
actor_parameters_changed: false
```

## Metric Interpretation

The exact reconstruction succeeded:

```text
sample_reconstruction_success_rate >= 0.98: pass
metadata_missing_rows == 0: pass
missing_normal_rows == 0: pass
missing_source_snapshots == 0: pass
actor_parameters_changed == false: pass
```

The current checkpoint has a non-degenerate intervention gap:

```text
normal_intervention_gap_mean: 0.024908
normal_intervention_gap_p10: 0.021141
target_gap_mean: 0.041716
gap_deficit_mean: 0.016809
```

The objective is therefore not degenerate, but it is not a complete hard-negative
contrast objective:

```text
hard_negative_available_fraction: 0.721352
```

This matches M755/M756: the positive-plus-normal objective path is valid, while
hard-negative calibration must remain optional or be repaired by later mining.

## Variant And Horizon Metrics

Variant metrics:

```text
zero_command_obs:
  rows: 1044
  gap_mean: 0.025399
  target_gap_mean: 0.044269
  hard_negative_available_fraction: 0.838123

reset_hidden_each_step:
  rows: 169
  gap_mean: 0.021873
  target_gap_mean: 0.025947
  hard_negative_available_fraction: 0.0
```

Horizon metrics:

```text
H=2:
  rows: 25
  gap_mean: 0.025215
  hard_negative_available_fraction: 1.0

H=4:
  rows: 168
  gap_mean: 0.024878
  hard_negative_available_fraction: 1.0

H=6:
  rows: 455
  gap_mean: 0.025016
  hard_negative_available_fraction: 0.753846

H=8:
  rows: 565
  gap_mean: 0.024816
  hard_negative_available_fraction: 0.6
```

## Failure Taxonomy

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
Exact reconstruction and metrics pass, but hard-negative availability remains
sparse. This is inherited from M755 and must not be hidden by the objective
sanity result.
```

Not failures:

```text
not reconstruction_blocked
not metadata_artifact
not objective_degenerate
not contract_violation
not proof_washout
not promotion_gate_failure
not training_instability
```

## Artifacts

```text
runs/m758_v4_sequence_objective_sanity/summary.json
runs/m758_v4_sequence_objective_sanity/objective_rows.csv
runs/m758_v4_sequence_objective_sanity/objective_metrics.csv
runs/m758_v4_sequence_objective_sanity/rejected_rows.csv
```

## Next Decision

M759 should audit M758 before any actor-update implementation.

The audit should decide whether to:

```text
1. design a no-PPO objective-only probe with exact gates;
2. repair hard-negative sparsity before any actor coupling;
3. keep objective work positives-plus-normal only;
4. return to scenario mining or simulator fidelity.
```
