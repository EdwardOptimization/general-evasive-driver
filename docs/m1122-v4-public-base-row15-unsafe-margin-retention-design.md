# M1122 V4 Public Base Row15 Unsafe-Margin Retention Design

## Purpose

M1122 designs the next repair after M1121 showed that row15 was covered by the
M1115 target-base rejected-history trajectory anchor but still crossed
wrong-history terminal margin in M1120.

This milestone is design-only. It does not train actor weights, run PPO, run
replay, mine rows, promote a checkpoint, use private holdout, or change actor
inputs.

## Diagnosis To Preserve

M1121 established:

```text
row_id: 15
physical_pair_key: 9530:21:9550:21
row15 target-base anchor rows: 170
target-base-only trajectory MSE for m1118_seed111800: 0.000001498
target-base-only MSE threshold: 0.000100000
normal_lost_events in M1120: 0
wrong_history_safe_events in M1120: 4
```

Therefore the next repair should not be "increase generic action anchor
pressure". The row is already action-close. The missing constraint is:

```text
under wrong history, row15 terminal margin must remain negative with slack;
under normal history, row15 terminal margin must remain positive.
```

This is a closed-loop terminal-margin constraint, not a one-step action MSE
constraint.

## Design Decision

Use a lexicographic unsafe-margin projection probe rather than another actor
optimizer.

The M1118 update direction is useful but too large for row15. M1123 should
construct interpolation candidates between the current public base and
`m1118_seed111800`:

```text
theta_alpha = theta_base + alpha * (theta_m1118 - theta_base)
```

Because M1118 changed only the allowed actor-coupling tensors, this projection
should still be contract-clean after a parameter-diff audit. M1123 must still
verify that only these tensors differ from base:

```text
response_context_fusion.0.weight
response_context_fusion.0.bias
actor_mean.weight
actor_mean.bias
```

Candidate alphas:

```text
0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1.0
```

If no nonzero alpha passes, M1123 should reject the M1118 direction and route to
a new objective design. It should not keep adding generic anchor pressure.

## Lexicographic Acceptance

M1123 should evaluate candidates in this order.

### 1. Contract and exact objective

Required:

```text
actor inputs unchanged
parameter changes limited to the allowed actor-coupling tensors
exact M1107 loss <= base exact M1107 loss
exact M1107 improvement > 0 for any candidate selected for replay
target-base-only trajectory-anchor MSE <= 0.0001
combined trajectory-anchor MSE <= 0.0001
```

The selected alpha must be nonzero. Alpha `0.0` is only the baseline reference.

### 2. Row15 unsafe-margin gate

Evaluate row15 variants from the existing target-base surfaces:

```text
m223_m219 row15
m267_m264 row15
current_m333_surface row15
m314_continuity_surface row15
m317_continuity_surface row15
```

Required for every row15 variant:

```text
normal_success == true
normal_margin >= 0.0
wrong_history_success == false
wrong_history_margin <= unsafe_margin_threshold
```

Use a per-row threshold:

```text
unsafe_margin_threshold = min(-0.00025, 0.5 * base_wrong_history_margin)
```

Since `base_wrong_history_margin` is negative, this keeps at least half of the
base unsafe slack where possible and prevents accepting a row that is only
epsilon-negative.

### 3. First replay gate

If a nonzero alpha passes row15 unsafe-margin and exact gates, M1123 should run
the same six-surface first replay used in M1120 for the selected alpha:

```text
m183_m168
m223_m219
m267_m264
current_m333_surface
m314_continuity_surface
m317_continuity_surface
```

The thresholds remain unchanged:

```text
max_continuation_steps: 60
max_normal_success_drop: 0.0
max_normal_margin_regression: 0.005
max_margin_gap_regression: 0.001
max_success_drop_count_regression: 0
```

M1123 must not proceed to family-intersection replay, full public gate,
fresh/OOD, behavior gates, PPO, or promotion.

## Selection Rule

Among nonzero alphas that satisfy the contract, exact, row15 unsafe-margin, and
six-surface first replay gates, select the largest alpha.

If multiple alphas pass row15 but the selected first replay fails, reject the
probe and route to failure audit. Do not try additional alphas after seeing the
first replay unless that retry was pre-registered in a new manifest.

If no nonzero alpha passes row15 unsafe-margin:

```text
result_class: row15_unsafe_margin_projection_no_candidate
next: objective redesign or terminal-margin target export
```

If a nonzero alpha passes row15 but first replay fails:

```text
result_class: row15_unsafe_margin_projection_first_replay_failed
next: failure audit
```

If a nonzero alpha passes row15 and first replay:

```text
result_class: row15_unsafe_margin_projection_first_replay_candidate
next: family-intersection replay design only
```

No result in M1123 is promotable.

## Why This Is Not Just Another Gate-Passing Loop

The scientific link being tested is narrow but necessary:

```text
Can we keep exact objective movement while explicitly preserving the
counterfactual wrong-history unsafe outcome on the known terminal-margin cliff?
```

M1123 does not claim driver improvement, generalization, or level3
self-identification. It only tests whether the M1118 useful direction has a
nonzero trust region that preserves the row15 terminal proof.

If it does not, the branch should stop trying to salvage this direction with
more MSE anchors and should synthesize before opening a new objective branch.

## Decision

```text
row15_unsafe_margin_retention_design_admit_projection_probe
```

Next milestone:

```text
m1123-v4-public-base-row15-unsafe-margin-projection-probe
```
