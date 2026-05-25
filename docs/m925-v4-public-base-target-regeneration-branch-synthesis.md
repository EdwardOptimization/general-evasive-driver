# M925 V4 Public-Base Target Regeneration Branch Synthesis

## Purpose

M925 synthesizes the `v4_public_base_target_regeneration` branch before adding
another narrow residual-objective variant.

This synthesis covers M916-M924.

M925 is process-only:

```text
no training
no target generation
no M880 exact compatibility
no replay
no PPO
no checkpoint promotion
```

## Evidence Summary

M916 designed M399-rooted target regeneration after the previous public-base
integration branch showed that stale M568/M761 targets did not transfer.

M917 implemented strict low-tail target generation:

```text
selected_sources: 67
accepted_targets: 67
distinct_seeds: 19
max_fault_family_pair_fraction: 0.3582089552238806
result_class: public_base_target_regeneration_too_few_targets
```

The target search worked on selected rows, but the strict low-tail source pool
was too sparse and concentrated.

M918 designed source expansion. M919 implemented it and passed source gates:

```text
accepted_targets: 122
strict_low_tail_accepted_targets: 103
near_tail_accepted_targets: 19
distinct_seeds: 26
distinct_fault_family_pairs: 14
max_fault_family_pair_fraction: 0.19672131147540983
result_class: public_base_expanded_target_regeneration_pass
```

M920 designed a regenerated-target residual objective. M921 implemented it:

```text
reconstructed_rows: 1213 / 1213
joined_target_rows: 122 / 122
candidate_alpha_count: 0
actor_backbone_changed: false
```

M921 improved target-action MSE but did not deliver enough low-tail lift inside
normal-retention alphas.

M922 audited M921 as `objective_overfit` and routed to an alpha-aware
low-tail objective.

M923 designed that objective. M924 implemented it:

```text
candidate_alpha_count: 0
alpha 0.35 low_tail_fraction: 0.30090683698654175
alpha 0.35 normal_retention_pass: false
alpha 1.0 tail_lift_pass: true
alpha 1.0 normal_retention_pass: false
```

M924 strongly improved low-tail metrics, but all useful alphas violated
normal-retention gates and target-action alignment worsened.

## Supported Claims

The branch supports:

```text
1. M399-rooted target generation can produce source-diverse regenerated target
   rows after near-tail source expansion.
2. The regenerated target corpus joins cleanly to the full reconstruction
   corpus.
3. Frozen-M399 residual-head training is runnable and preserves the actor
   backbone.
4. Target-action imitation can improve target MSE but does not solve low-tail
   lift inside normal-retention gates.
5. Alpha-aware low-tail losses can move the low-tail metrics, but current
   residual directions leave the normal-retention trust region.
```

## Falsified Claims

The branch falsifies:

```text
1. Strict low-tail-only source mining is enough for target generation.
2. Regenerated target-action imitation alone is enough to admit a residual
   candidate.
3. Direct low-tail objective pressure alone is enough to admit a candidate
   under the existing normal-retention envelope.
4. The public-base target-regeneration failure is caused by target scarcity or
   reconstruction failure.
```

## Failure Taxonomy Summary

Observed:

```text
scenario_sampling_failure:
  M917 strict low-tail source pool cannot satisfy the seed-diversity gate.

objective_overfit:
  M921 target-action objective improves target MSE but not the full low-tail
  candidate gate.

promotion_gate_failure:
  M924 low-tail metrics improve only outside the normal-retention trust region,
  so no alpha can be admitted toward exact compatibility.
```

Not observed:

```text
contract_violation
lineage_invalid
training_instability
metric_artifact
PPO washout
replay regression
```

## Public Gate Overfit Risk

This branch used public artifacts only and makes no promotion or paper-quality
claim. It has not run M880 exact compatibility, replay, PPO, or private
holdouts.

The risk is now active-set overfitting to the M912/M919 public objective rows.
Before another residual-objective variant, the next branch should test
feasibility of the residual directions and trust-region envelope directly.

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Close:

```text
v4_public_base_target_regeneration
```

Open:

```text
v4_public_base_trust_region_feasibility
```

Next:

```text
m926-v4-public-base-residual-direction-feasibility-design
```

The next branch should first run no-training feasibility analysis over existing
residual directions and gates:

```text
Can any interpolation, alpha schedule, or row-local active set satisfy both
normal-retention and low-tail lift before more objective training?
```

If not, the project should stop treating a single global residual head as the
right public-base bridge and return to policy-level or corpus-level strategy.
