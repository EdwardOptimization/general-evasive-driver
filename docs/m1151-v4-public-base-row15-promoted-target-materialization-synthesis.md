# M1151 V4 Public Base Row15 Promoted Target Materialization Synthesis

## Purpose

M1151 synthesizes the `row15_promoted_target_materialization` branch before any
new repair design, replay escalation, PPO, or promotion.

Scope:

```text
branch: row15_promoted_target_materialization
evidence window: M1142-M1150
allowed action: synthesis only
```

No actor training, PPO, replay, mining, promotion, private holdout, or
actor-input change occurs in this milestone.

## Evidence Summary

M1142 successfully materialized the all-policy-pass promoted-base surface under
the current public-gate base:

```text
rows: 148
normal_success_count: 148
wrong_history_success_count: 0
success_drop_count: 148
physical_pairs: 13
source_labels: 5
targets: 2
left_steps: 6
min_normal_margin: 0.000998
max_wrong_history_margin: -0.000063
min_margin_gap: 0.001314
```

M1144 converted the materialized surface into a deduplicated objective corpus
and proved the objective has learnable signal:

```text
corpus_rows: 76
physical_pairs: 13
targets: 2
success_drop_rows: 76
objective_pass: true
seed_pass_count: 3
mean_val_combined_loss_improvement: 3.211031
mean_val_pairwise_accuracy_after: 1.0
```

M1147 then produced a contract-clean actor-coupling candidate:

```text
best candidate: m1147_114602
base exact M1144 loss: 0.417700
candidate exact M1144 loss: 0.409408
exact delta: -0.008292
changed tensors: actor_mean.* and response_context_fusion.0.* only
log_std changed: false
```

M1149 rejected that candidate at first replay:

```text
surface_count: 10
passed_surface_count: 8
failed_surface_count: 2
lost_success_drop_events: 76
normal_lost_events: 0
wrong_history_safe_events: 76
```

M1150 classified the mechanism:

```text
all materialized failed geometries covered by M1144: true
m267 failure present in M1144 objective: false
failed-row weight mean: 0.003962
nonfailed-row weight mean: 0.015196
failed-row wrong-history margin mean: -0.000463
nonfailed-row wrong-history margin mean: -0.004114
diagnosis: objective-form insufficiency
```

## Supported Claims

This branch supports the following limited claims:

```text
1. The current public-gate base has a source-diverse promoted-row15 materialized
   surface with 148 target-policy success-drop rows.

2. A deduplicated 76-row objective corpus built from that surface has strong
   supervised/preference signal under exact objective sanity.

3. A very small actor-coupling update can improve the exact M1144 objective
   while staying inside the allowed actor parameter surface.

4. The first-replay gate is necessary: exact objective improvement alone is not
   sufficient to preserve self-ID proof rows.

5. The dominant failure mode is wrong-history branches becoming safe while
   normal-history success is retained.
```

## Falsified Claims

This branch falsifies the following stronger claims:

```text
1. Direct M1144 exact-objective actor updates are replay-safe.

2. Coverage of failed materialized geometries in the objective corpus is enough
   to preserve wrong-history unsafe outcomes.

3. Generic action/snippet anchors and allowed-parameter scope are enough to
   prevent terminal-margin proof washout.

4. M1147 should proceed to family-intersection replay, behavior gates, PPO, or
   promotion.

5. This branch proves level3 anticipatory self-identification, paper-level
   generalization, or real-vehicle readiness.
```

## Failure Taxonomy Summary

```text
primary failure type: proof_washout
mechanism: wrong_history_safe_terminal_margin_crossing
normal-history collapse: false
actor contract violation: false
optimizer instability: false
materialized objective coverage miss: false
metric artifact: false
```

The failure is specifically an objective-form mismatch:

```text
M1144 objective:
  preference/log-probability improvement on selected hidden/action snippets

M1149/M1150 proof requirement:
  closed-loop wrong-history terminal margin must remain negative on
  near-boundary braking rows while normal-history success is retained
```

## Public-Gate Overfit Risk

The branch reduced one overfit risk but exposed another.

Reduced risk:

```text
The row15-promoted surface is not a stale singleton. It spans 13 physical
pairs, 5 source labels, 2 targets, and 6 left steps.
```

Remaining risk:

```text
The actor update was optimized against a fixed public 76-row objective corpus.
The failed rows are all public proof rows, and further tuning directly against
them can overfit the proof surface unless the next branch uses strict
lexicographic gates and stops at proof repair rather than claiming capability.
```

Mitigation:

```text
1. Treat the next branch as proof repair only.
2. Require exact M1144 no-regression plus explicit wrong-history unsafe-margin
   retention on M1149 failed rows.
3. Keep M267 old-public row15 retention explicit.
4. Run first replay before any family/behavior/full-public escalation.
5. Do not use private holdout in this repair branch.
```

## Next Branch Decision

The branch should close.

```text
closed_branch: row15_promoted_target_materialization
opened_branch: row15_promoted_unsafe_margin_projection
synthesis_decision: promote_to_next_branch
```

The next branch should not start with another actor update. It should first
design a no-training unsafe-margin projection probe over the M1147 direction:

```text
base checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt

candidate direction:
  runs/m1147_row15_promoted_actor_coupling_anchor100_s10_lr5e5_seed114602/optimized_checkpoint.pt

primary acceptance:
  exact M1144 objective non-regression/improvement
  M1149 failed wrong-history margins remain negative under a registered
    unsafe-margin rule
  M267 old-public row15 remains unsafe under wrong history
  normal-history success remains 1.0 on the checked rows
```

No PPO, promotion, family-intersection replay, behavior gate, private holdout,
or actor-input change is admitted by this synthesis.

## Decision

```text
decision: row15_promoted_target_materialization_synthesis_open_unsafe_margin_projection
next: m1152-v4-public-base-row15-promoted-unsafe-margin-projection-design
```
