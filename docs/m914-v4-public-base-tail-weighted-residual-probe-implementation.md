# M914 V4 Public-Base Tail-Weighted Residual Probe Implementation

## Purpose

M914 implements and runs the M913 design: train only a tail-weighted residual
head on frozen M399 public-base recurrent actor features.

M914 does not update the actor, run M880 exact compatibility, run replay, run
PPO, or promote.

## Implementation

M914 adds:

```text
src/autodrift/public_base_tail_weighted_residual_probe.py
tests/test_public_base_tail_weighted_residual_probe.py
```

The implementation:

```text
loads M399 public-base checkpoint;
freezes every actor parameter;
reconstructs M755 sequence samples;
joins M912 low-tail rows back to reconstructed samples;
assigns tail weights from low-tail membership and M909 near-base deficit;
trains only a bounded feature_dim=128 residual head;
exports alpha metrics with p10, deficit, low-tail fraction, normal-retention,
tail-lift, and candidate gates.
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.public_base_tail_weighted_residual_probe \
  --checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --corpus-summary runs/m755_v4_sequence_outcome_corpus_export/summary.json \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --low-tail-rows runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv \
  --m912-summary runs/m912_v4_public_base_sequence_recalibration_audit/summary.json \
  --m909-objective-rows runs/m909_v4_public_base_residual_head_probe/objective_rows.csv \
  --run-dir runs/m914_v4_public_base_tail_weighted_residual_probe \
  --device cpu \
  --epochs 40 \
  --seed 9140
```

## Result

Summary:

```text
result_class: public_base_tail_weighted_probe_no_candidate
positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
metadata_missing_rows: 0
missing_low_tail_keys: 0
rejected_rows: 0
residual_parameter_count: 8451
candidate_alpha_count: 0
actor_backbone_changed: false
residual_only_training: true
training_started: true
optimizer_started: true
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Actor checksum:

```text
before: 6942ee9be6ba7c3c65fd56ed7e307cbb82dc8b16bfe5db09b4642de5ce631c1d
after:  6942ee9be6ba7c3c65fd56ed7e307cbb82dc8b16bfe5db09b4642de5ce631c1d
```

## Alpha Metrics

Registered public-base near-base values:

```text
near_base_gap_p10: 0.0069862247444689276
near_base_gap_deficit_mean: 0.016876555956218328
near_base_low_tail_fraction: 0.4105523495465787
```

M914 result:

```text
alpha  retention  tail_lift  candidate  gap_p10   deficit_mean  low_tail_fraction
0.02   true       false      false      0.006975  0.016891      0.410552
0.10   true       false      false      0.007257  0.016564      0.405606
0.20   true       false      false      0.007710  0.016153      0.394889
0.35   false      false      false      0.008663  0.015536      0.390767
0.50   false      false      false      0.009623  0.014933      0.385820
0.75   false      false      false      0.010762  0.013965      0.369332
1.00   false      true       false      0.011928  0.013021      0.317395
```

The tail-weighted objective did move the low-tail metric at high alpha:

```text
low_tail_fraction: 0.410552 -> 0.317395
gap_deficit_mean: 0.016877 -> 0.013021
```

But this happens only after normal retention fails:

```text
alpha 1.0 normal_retention_pass: false
first_action_drift_from_base_mean: 0.008672
first_action_drift_from_base_p95: 0.019852
```

Inside the normal-retention region, no alpha passes the tail-lift gate.

## Interpretation

M914 shows that the low-tail rows are movable by residual action changes, but
not within the registered normal-retention envelope using the stale M755/M758
target structure.

This is not:

```text
feature_dim mismatch;
actor-input contract violation;
sample reconstruction failure;
low-tail join failure;
actor mutation;
PPO washout.
```

The remaining blocker is target/action lineage. The old target structure can
pressure the residual head in the right direction only when action drift becomes
too large. That is not acceptable for a public-base integration path.

## Supported Claims

M914 supports:

```text
1. Tail weighting was implemented and exercised on the full reconstructed
   M399 sequence corpus.
2. The M399 actor remained unchanged.
3. Low-tail metrics improve at high alpha.
4. No admissible alpha exists under the registered normal-retention plus
   tail-lift gates.
```

## Unsupported Claims

M914 does not support:

```text
tail-weighted residual candidate;
M880 exact compatibility;
replay retention;
PPO safety;
checkpoint promotion.
```

## Decision

Decision:

```text
public_base_tail_weighted_probe_no_candidate_route_to_branch_synthesis_then_target_regeneration
```

Next:

```text
m915-v4-public-base-integration-readiness-branch-synthesis
```

The branch has reached its synthesis cadence. M915 should synthesize
M905-M914, then open a new M399-rooted target-regeneration branch instead of
continuing to tune tail weights or epochs on the stale M755/M758 targets.
