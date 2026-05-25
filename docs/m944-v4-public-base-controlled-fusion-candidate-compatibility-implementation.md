# M944 V4 Public Base Controlled Fusion Candidate Compatibility Implementation

## Purpose

M944 implements the M943 exact no-update compatibility design. It materializes
the M942 candidate alphas as ordinary loadable checkpoints and re-runs exact
objective metrics from those checkpoints.

M944 does not train, run replay, run PPO, use private holdout, or promote.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_controlled_fusion_candidate_compatibility \
  --base-checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --raw-checkpoint runs/m940_v4_public_base_controlled_fusion_boundary_objective/checkpoints/raw_boundary_objective_update.pt \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --target-rows runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv \
  --m912-summary runs/m912_v4_public_base_sequence_recalibration_audit/summary.json \
  --low-tail-rows runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv \
  --run-dir runs/m944_v4_public_base_controlled_fusion_candidate_compatibility \
  --device cpu \
  --candidate-alphas 0.0675,0.0700,0.0725 \
  --primary-alpha 0.0725
```

## Artifacts

- Summary:
  `runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/summary.json`
- Candidate compatibility table:
  `runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/candidate_compatibility.csv`
- Interpolation manifest:
  `runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/manifest.json`
- Materialized candidate checkpoints:

```text
runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0675.pt
runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_07.pt
runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0725.pt
```

## Result

M944 passes exact no-update compatibility for all three candidates.

```text
primary_alpha: 0.0725
materialized_checkpoint_count: 3
expected_checkpoint_count: 3
exact_candidate_count: 3
primary_candidate_exact_pass: true
backup_candidate_exact_pass_count: 2
forbidden_parameter_changed: false
training_started: false
optimizer_started: false
replay_used: false
ppo_used: false
promoted: false
exact_no_update_used: true
result_class: public_base_controlled_fusion_candidate_compatibility_primary_candidate
```

The primary checkpoint is:

```text
runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0725.pt
```

## Primary Candidate Metrics

The primary materialized checkpoint reproduces the M942 candidate metrics when
evaluated as a normal checkpoint at exact alpha `1.0`:

```text
normal_retention_pass: true
tail_lift_pass: true
target_loss_pass: true
target_tolerance_pass: true
first_action_drift_from_base_mean: 0.0026981827
first_action_drift_from_base_p95:  0.0064748540
normal_anchor_mse_mean:            0.0000038589
normal_anchor_mse_p95:             0.0000139746
normal_intervention_gap_p10:       0.0113417562
gap_deficit_mean:                  0.0129708514
low_tail_fraction:                 0.3264633119
target_action_mse_mean:            0.0005227432
```

Backup candidates also pass:

```text
alpha 0.0675: exact_candidate_pass true
alpha 0.0700: exact_candidate_pass true
```

## Interpretation

M944 removes the in-memory interpolation concern. The controlled-fusion
candidate survives ordinary checkpoint materialization and load-time exact
re-evaluation.

This is still not a closed-loop replay result. It only means the candidate is
ready for a no-training replay/proof-retention design.

## Decision

Do not promote M944. Do not run PPO from M944 yet.

Next route:

```text
replay/proof-retention design for the primary materialized checkpoint
```

M945 should design the first replay/proof retention pass for:

```text
runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0725.pt
```

Next blocker:

```text
m945-v4-public-base-controlled-fusion-candidate-replay-gate-design
```
