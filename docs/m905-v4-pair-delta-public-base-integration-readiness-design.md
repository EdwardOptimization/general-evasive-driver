# M905 V4 Pair-Delta Public-Base Integration Readiness Design

## Purpose

M905 designs the route from the M568-rooted pair-delta objective signal toward
the current public-gate base lineage.

M905 is design-only:

```text
no exact recheck execution
no actor update
no replay execution
no PPO
no checkpoint promotion
```

## Bases Must Stay Separate

Current public-gate base:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

Diagnostic BC base used by M895-M904:

```text
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

M568-rooted raw candidates:

```text
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt
runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/raw_candidate.pt
```

These raw candidates are evidence for the objective direction. They are not
public-gate driver checkpoints.

## Integration Readiness Sequence

Public-base integration must proceed in stages:

```text
M906: exact no-update compatibility audit for M399 public base
M907: objective-only public-base probe design if M906 passes
M908+: execute public-base objective-only probe with exact holdout interpolation
later: replay, behavior, fresh, and challenge gates
never: direct PPO or promotion from M568-rooted raw candidates
```

## M906 Exact Compatibility Audit

M906 should run exact no-update objective sanity on the current public-gate base:

```text
checkpoint:
  runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt

residual head:
  runs/m761_v4_sequence_objective_probe/residual_head.pt

scenario config:
  configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json

objective rows:
  runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_train_public_rows.csv
  runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_eval_public_rows.csv
  runs/m880_v4_pair_delta_objective_target_enrichment/enriched_source_holdout_public_rows.csv
  runs/m880_v4_pair_delta_objective_target_enrichment/enriched_new_signature_holdout_public_rows.csv
```

M906 pass conditions:

```text
tensor_rows_reconstructed: 247 / 247
missing_tensor_count: 0
exact_losses_finite: true
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
actor_parameters_changed: false
```

M906 does not need to improve exact objective metrics. It only answers:

```text
Can the public-gate base be evaluated on the same pair-delta objective surface
without reconstruction, contract, or metric failure?
```

## After M906

If M906 passes, the next design can specify a public-base objective-only probe:

```text
train only a narrow actor-coupling scope;
keep M761 residual head fixed;
use exact before/after metrics;
interpolate from M399 public base to raw candidate;
reject exact holdout regression;
keep M568 raw candidates diagnostic-only;
run replay/behavior/fresh gates before any integration claim;
block PPO and promotion.
```

If M906 fails:

```text
route to public-base reconstruction compatibility audit;
do not attempt actor update;
do not modify actor inputs to force compatibility.
```

## Decision

Decision:

```text
public_base_integration_readiness_design_admit_m906
```

Next:

```text
m906-v4-pair-delta-public-base-exact-compatibility-audit
```

M906 may run exact no-update objective sanity for the current public-gate base.
It must not train, run PPO, run replay, or promote.
