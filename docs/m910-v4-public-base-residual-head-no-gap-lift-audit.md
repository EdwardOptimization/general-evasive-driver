# M910 V4 Public-Base Residual-Head No-Gap-Lift Audit

## Purpose

M910 audits the M909 result before allowing the generated M399 residual head to
be used in any M880 exact compatibility, replay, PPO, or promotion path.

M910 is audit-only:

```text
no training
no M880 exact execution
no replay
no PPO
no checkpoint promotion
no actor input change
```

## M909 Result Recap

M909 compatibility succeeded:

```text
checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
reconstructed_rows: 1213 / 1213
metadata_missing_rows: 0
rejected_rows: 0
actor_backbone_changed: false
residual_only_training: true
residual_head feature_dim: 128
residual_parameter_count: 8451
ppo_used: false
promoted: false
```

M909 objective admissibility failed:

```text
result_class: v4_sequence_objective_probe_no_gap_lift
candidate_alpha_count: 0
candidate_alphas: []
```

## M761 vs M909 Comparison

M761, rooted at M568, produced admitted alphas:

```text
alpha  retention  gap_lift  candidate  drift_mean  gap_p10   deficit_mean
0.20   true       true      true       0.000480    0.023874  0.012637
0.50   true       true      true       0.001200    0.025665  0.006068
1.00   true       true      true       0.002401    0.028827  0.000000337
```

M909, rooted at M399, produced no admitted alpha:

```text
alpha  retention  gap_lift  candidate  drift_mean  gap_p10   deficit_mean
0.02   true       false     false      0.000205    0.006986  0.016877
0.10   true       false     false      0.001024    0.007314  0.016492
0.20   true       false     false      0.002048    0.007860  0.016010
0.50   false      false     false      0.005121    0.009969  0.014624
1.00   false      false     false      0.010242    0.012391  0.012462
```

The important pattern:

```text
M909 normal_intervention_gap_mean is already large, around 0.144-0.150.
M909 normal_intervention_gap_p10 stays low, around 0.007-0.012.
M909 gap_deficit_mean remains above the registered lift threshold.
Increasing alpha eventually breaks normal retention before the low tail is fixed.
```

## Interpretation

M909 is not blocked by feature dimension anymore. It generated a valid 128-dim
residual head and kept the M399 actor unchanged.

The blocker is objective/target lineage:

```text
M755/M758/M761 thresholds and target gaps were calibrated around M568/M761.
M399 has a different feature basis and behavior distribution.
The old objective rewards broad gap movement, but M399's failure is low-tail
gap coverage and deficit concentration.
```

This means the next step should not be:

```text
run M880 exact with M909 head;
rerun the same residual objective with more epochs;
increase residual alpha;
run replay;
run PPO;
promote anything.
```

The M909 head exists as an artifact, but it is not admitted for downstream
M880 exact compatibility because the registered candidate gate failed.

## Route Decision

Rejected route:

```text
Use M909 residual head in M880 exact compatibility immediately.
```

Reason:

```text
candidate_alpha_count is zero; M909 did not produce an admitted residual
candidate under the registered sequence objective gates.
```

Rejected route:

```text
Rerun M909 with larger alpha or treat alpha 1.0 as useful.
```

Reason:

```text
alpha 1.0 still fails gap lift and also fails normal retention. The issue is
not simply that alpha was too small.
```

Deferred route:

```text
Residual-free public-base exact sanity.
```

Reason:

```text
It may be useful later, but the immediate evidence says the public-base
sequence objective needs recalibration around M399's low-tail rows and target
definitions.
```

Selected route:

```text
m911-v4-public-base-sequence-objective-recalibration-design
```

M911 should design a no-training public-base recalibration step that:

```text
uses M399 as the base actor;
computes M399-specific baseline gap, p10, deficit, and row-level low-tail sets;
separates mean-gap-large rows from low-tail-deficit rows;
decides whether to regenerate public-base target rows or write a tail-weighted
residual objective;
keeps M568/M761 thresholds diagnostic-only;
blocks replay, PPO, actor update, and promotion.
```

## Supported Claims

M910 supports:

```text
1. M909 solved the feature_dim compatibility construction but not objective
   admissibility.
2. The old M761-style objective/gates do not transfer cleanly to M399.
3. M399 needs public-base-specific sequence objective recalibration or target
   regeneration before any M880 exact integration.
```

## Unsupported Claims

M910 does not support:

```text
M909 residual-head downstream use;
M880 exact compatibility;
actor update feasibility;
replay retention;
generalization improvement;
PPO safety;
checkpoint promotion.
```

## Decision

Decision:

```text
public_base_residual_head_no_gap_lift_route_to_sequence_recalibration_design
```

Next:

```text
m911-v4-public-base-sequence-objective-recalibration-design
```

M911 should be design-only and must not train, run M880 exact compatibility,
run replay, run PPO, or promote.
