# M924 V4 Public-Base Alpha-Aware Low-Tail Residual Probe Implementation

## Purpose

M924 implements and runs the alpha-aware low-tail residual objective designed
in M923.

Allowed:

```text
train only a residual head on frozen M399 features
evaluate objective metrics
```

Forbidden:

```text
M399 actor-backbone update
actor-input change
M880 exact compatibility
replay
PPO
checkpoint promotion
```

## Implementation

M924 adds:

```text
src/autodrift/public_base_alpha_aware_low_tail_residual_probe.py
tests/test_public_base_alpha_aware_low_tail_residual_probe.py
```

The objective evaluates low-tail losses at train alphas:

```text
0.20, 0.35
```

Loss components:

```text
low-tail gap floor loss
low-tail deficit loss
soft low-tail fraction surrogate
target-action auxiliary
normal anchor
intervention anchor
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_alpha_aware_low_tail_residual_probe \
  --checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --regenerated-target-rows runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv \
  --m912-summary runs/m912_v4_public_base_sequence_recalibration_audit/summary.json \
  --low-tail-rows runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv \
  --m909-objective-rows runs/m909_v4_public_base_residual_head_probe/objective_rows.csv \
  --run-dir runs/m924_v4_public_base_alpha_aware_low_tail_residual_probe \
  --device cpu \
  --epochs 40 \
  --seed 9240
```

## Result

Summary:

```text
positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
metadata_missing_rows: 0
missing_target_keys: 0
regenerated_target_rows_count: 122
joined_target_rows: 122
low_tail_rows_count: 498
residual_parameter_count: 8451
train_alphas: 0.20, 0.35
candidate_alpha_count: 0
actor_backbone_changed: false
training_started: true
residual_only_training: true
m880_exact_used: false
replay_used: false
ppo_used: false
promoted: false
result_class: public_base_alpha_aware_low_tail_probe_no_candidate
```

M924 fails the candidate-alpha gate:

```text
candidate_alpha_count: 0
```

It is not a reconstruction, target-join, or actor-contract failure:

```text
reconstructed_rows: 1213 / 1213
joined_target_rows: 122 / 122
actor_backbone_changed: false
```

## Comparison With M921

M924 changes the failure mode.

M921 at alpha `0.35`:

```text
normal_retention_pass: true
tail_lift_pass: false
target_loss_pass: true
low_tail_fraction: 0.39323991537094116
gap_deficit_mean: 0.015976072219181237
```

M924 at alpha `0.35`:

```text
normal_retention_pass: false
tail_lift_pass: false
target_loss_pass: false
low_tail_fraction: 0.30090683698654175
gap_deficit_mean: 0.013196162368122547
```

M924 at alpha `1.00`:

```text
normal_retention_pass: false
tail_lift_pass: true
target_loss_pass: false
low_tail_fraction: 0.16652926802635193
gap_deficit_mean: 0.0076176024472797005
```

The alpha-aware objective strongly improves low-tail metrics, but it does so by
leaving the normal-retention trust region and by worsening target-action MSE.

## Interpretation

M924 supports that direct low-tail losses can move the desired tail metrics, but
the current residual-head direction is too global or too large for the
registered normal-retention envelope.

The failure is therefore not:

```text
source scarcity
target regeneration failure
residual-head training instability
actor-input contract violation
```

The failure is:

```text
trust-region conflict between low-tail lift and normal-action retention
```

## Decision

Decision:

```text
public_base_alpha_aware_low_tail_probe_no_candidate_route_to_branch_synthesis
```

Next:

```text
m925-v4-public-base-target-regeneration-branch-synthesis
```

Per the M924 fallback rule, the next step should synthesize the branch before
adding another narrow objective variant.

## Supported Claims

M924 supports:

```text
1. Alpha-aware low-tail losses are effective at moving low-tail metrics.
2. Those low-tail gains currently require action drift outside normal-retention
   gates.
3. The M919/M921/M924 pipeline preserves the M399 actor backbone and does not
   run exact compatibility, replay, PPO, or promotion.
```

## Unsupported Claims

M924 does not support:

```text
admitted residual-head alpha;
M880 exact compatibility;
replay retention;
PPO safety;
driver improvement;
checkpoint promotion.
```
