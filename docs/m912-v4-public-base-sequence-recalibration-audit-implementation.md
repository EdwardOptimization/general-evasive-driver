# M912 V4 Public-Base Sequence Recalibration Audit Implementation

## Purpose

M912 implements and runs the deterministic no-training recalibration audit
designed in M911.

M912 does not load model checkpoints, train, run M880 exact compatibility, run
replay, run PPO, or promote.

## Implementation

M912 adds:

```text
src/autodrift/public_base_sequence_recalibration_audit.py
tests/test_public_base_sequence_recalibration_audit.py
```

The audit reads saved M909/M761 CSV/JSON artifacts and writes:

```text
runs/m912_v4_public_base_sequence_recalibration_audit/summary.json
runs/m912_v4_public_base_sequence_recalibration_audit/alpha_comparison.csv
runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv
runs/m912_v4_public_base_sequence_recalibration_audit/group_deficit_summary.csv
```

## Command

```bash
PYTHONPATH=src python -m autodrift.public_base_sequence_recalibration_audit \
  --m909-summary runs/m909_v4_public_base_residual_head_probe/summary.json \
  --m909-alpha-metrics runs/m909_v4_public_base_residual_head_probe/alpha_metrics.csv \
  --m909-objective-rows runs/m909_v4_public_base_residual_head_probe/objective_rows.csv \
  --m761-summary runs/m761_v4_sequence_objective_probe/summary.json \
  --m761-alpha-metrics runs/m761_v4_sequence_objective_probe/alpha_metrics.csv \
  --run-dir runs/m912_v4_public_base_sequence_recalibration_audit
```

## Result

Summary:

```text
run_type: public_base_sequence_recalibration_audit
near_base_alpha: 0.02
near_base_alpha_is_exact_zero: false
near_base_rows: 1213
near_base_gap_p10: 0.0069862247444689276
near_base_gap_deficit_mean: 0.016876555956218328
low_tail_gap_threshold: 0.021141
low_tail_deficit_threshold: 0.02
residual_free_deficit_threshold: 0.014809
low_tail_rows: 498
low_tail_fraction: 0.4105523495465787
distinct_fault_family_pairs: 17
distinct_variants: 1
distinct_source_pools: 1
m909_result_class: v4_sequence_objective_probe_no_gap_lift
m909_candidate_alpha_count: 0
m761_result_class: v4_sequence_objective_probe_candidate
route_decision: public_base_tail_weighted_objective_design
training_started: false
model_checkpoint_loaded: false
m880_exact_used: false
replay_used: false
ppo_used: false
promoted: false
```

## Alpha Comparison

M912 makes the M910 qualitative diagnosis explicit:

```text
alpha  m761_p10  m909_p10  p10_delta    m761_deficit  m909_deficit
0.02   0.021296  0.006986  -0.014310    0.016405      0.016877
0.10   0.022490  0.007314  -0.015177    0.014758      0.016492
0.20   0.023874  0.007860  -0.016014    0.012637      0.016010
0.50   0.025665  0.009969  -0.015696    0.006068      0.014624
1.00   0.028827  0.012391  -0.016436    0.000000337  0.012462
```

M909 remains low-tail deficient even when mean gap is large.

## Low-Tail Coverage

M912 defines a low-tail row at near-base alpha `0.02` as:

```text
normal_intervention_gap < 0.021141
or
gap_deficit > 0.02
```

Result:

```text
low_tail_rows: 498 / 1213
low_tail_fraction: 0.4105523495465787
distinct_fault_family_pairs: 17
```

Top group examples:

```text
front_lateral_authority_drop->combined_fault, horizon 8:
  rows 58, low_tail_rows 32, low_tail_fraction 0.5517

brake_authority_drop->global_mu_drop, horizon 8:
  rows 59, low_tail_rows 31, low_tail_fraction 0.5254

front_lateral_authority_drop->combined_fault, horizon 6:
  rows 48, low_tail_rows 29, low_tail_fraction 0.6042
```

This falsifies the idea that the M909 failure is a sparse singleton or one bad
fault pair.

## Route Decision

M912 selects:

```text
public_base_tail_weighted_objective_design
```

Reason:

```text
low_tail_rows >= 100
distinct_fault_family_pairs >= 3
distinct_variants >= 1
distinct_source_pools >= 1
```

The low-tail set is broad enough to justify a tail-weighted public-base
objective design. Target regeneration remains a fallback, but it is not the
immediate next route.

## Supported Claims

M912 supports:

```text
1. M909's no-gap-lift is a broad low-tail objective failure.
2. The low-tail failure covers many fault-family pairs.
3. A tail-weighted objective design is the next highest-leverage route.
4. No training, model loading, exact compatibility, replay, PPO, or promotion
   occurred in M912.
```

## Unsupported Claims

M912 does not support:

```text
tail-weighted objective success;
new residual-head candidate;
M880 exact compatibility;
replay retention;
PPO safety;
checkpoint promotion.
```

## Decision

Decision:

```text
public_base_sequence_recalibration_audit_route_to_tail_weighted_objective_design
```

Next:

```text
m913-v4-public-base-tail-weighted-objective-design
```

M913 should design a public-base residual objective that explicitly emphasizes
the M912 low-tail rows while preserving normal-retention safeguards.
