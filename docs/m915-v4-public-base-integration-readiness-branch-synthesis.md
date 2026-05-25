# M915 V4 Public-Base Integration Readiness Branch Synthesis

## Purpose

M915 synthesizes the `v4_pair_delta_public_base_integration_readiness` branch
before opening another target-regeneration branch.

This synthesis is required by the workflow cadence. It covers M905-M914.

M915 is process-only:

```text
no training
no target generation
no M880 exact compatibility
no replay
no PPO
no checkpoint promotion
```

## Evidence Summary

M905 separated the current public-gate base from the diagnostic BC branch:

```text
public-gate base: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
diagnostic BC base: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

M906 attempted direct public-base exact compatibility with the M761 residual
head and failed before reconstruction:

```text
M761 residual feature_dim: 64
M399 actor feature_dim: 128
```

M907 confirmed this is not an actor-input contract violation. Both M399 and
M568 use the P0 human-view 72-dim online GRU contract. The mismatch is the
internal actor feature basis.

M908 designed a public-base-compatible residual-head route. M909 implemented it
and trained a 128-dim residual head on frozen M399 features:

```text
reconstructed_rows: 1213 / 1213
metadata_missing_rows: 0
residual_parameter_count: 8451
actor_backbone_changed: false
candidate_alpha_count: 0
```

M910 audited the no-gap-lift result as an objective/target-lineage blocker, not
a feature-dim or input-contract issue.

M911 designed deterministic public-base recalibration. M912 implemented it and
found broad low-tail deficit:

```text
near_base_alpha: 0.02
near_base_gap_p10: 0.0069862247444689276
near_base_gap_deficit_mean: 0.016876555956218328
low_tail_rows: 498 / 1213
low_tail_fraction: 0.4105523495465787
distinct_fault_family_pairs: 17
route_decision: public_base_tail_weighted_objective_design
```

M913 designed a tail-weighted residual objective. M914 implemented it and still
found no admissible alpha:

```text
candidate_alpha_count: 0
alpha 1.0 low_tail_fraction: 0.317395
alpha 1.0 tail_lift_pass: true
alpha 1.0 normal_retention_pass: false
```

The tail-weighted objective can move low-tail metrics, but only with action
drift outside the normal-retention envelope.

## Supported Claims

The branch supports:

```text
1. M568/M761 residual features cannot be directly used with M399.
2. The issue is internal feature basis, not actor input contract.
3. M399 can reconstruct the sequence corpus and train a 128-dim residual head.
4. M761-style M755/M758 targets do not yield an admissible M399 residual
   candidate.
5. M399 low-tail deficit is broad, not a singleton artifact.
6. Tail weighting moves low-tail metrics but not within normal-retention gates.
```

## Falsified Claims

The branch falsifies:

```text
1. Direct M761 residual-head reuse is sufficient for public-base integration.
2. A simple 128-dim retraining of the M761-style residual objective is enough.
3. Tail weighting alone fixes M399 low-tail deficits under normal retention.
4. The M909/M914 failures are caused by actor-input contract violation.
```

## Failure Taxonomy Summary

Observed:

```text
lineage_invalid:
  M761 residual head is tied to M568 feature_dim 64 and cannot load into M399.

objective_overfit:
  M755/M758/M761 targets are useful diagnostic lineage but do not transfer into
  a normal-retaining M399 residual candidate.

metric_artifact risk:
  M761 thresholds cannot be reused as public-base pass gates without explicit
  recalibration.
```

Not observed:

```text
contract_violation
training_instability
PPO washout
replay regression
promotion_gate_failure
```

## Public Gate Overfit Risk

The branch still uses public workflow artifacts. It did not use private
holdouts and makes no promotion or paper-quality claim.

The next branch must avoid repeatedly tuning stale M755/M758 targets. It should
regenerate M399-rooted target rows or fresh source rows before attempting
another residual candidate.

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Close:

```text
v4_pair_delta_public_base_integration_readiness
```

Open:

```text
v4_public_base_target_regeneration
```

Next:

```text
m916-v4-public-base-target-regeneration-design
```

The next branch should design M399-rooted source mining and target regeneration
before any more residual training, M880 exact compatibility, replay, PPO, or
promotion.
