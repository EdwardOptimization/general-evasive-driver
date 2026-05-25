# M941 V4 Public Base Controlled Fusion Branch Synthesis

## Purpose

M941 synthesizes the controlled-fusion branch after M940. It does not train,
change actor inputs, run replay, run PPO, run private holdout, or promote.

The branch question is:

```text
Can the public-base low-tail gap be improved by updating only actor_mean and
response_context_fusion.0, without touching response/context encoders or GRU?
```

## Evidence Summary

M936 opened the controlled-fusion branch after actor_mean-only updates failed to
produce admissible tail lift.

M937 implemented the controlled trainable surface:

```text
allowed:
  actor_mean
  response_context_fusion.0

frozen:
  response_encoder
  context_encoder
  online_gru_cell
  critic
  log_std
  actor inputs
```

M937 showed clear low-tail leverage at high alpha, but no coarse-grid alpha
satisfied both normal retention and tail lift.

M938 ran a no-training fine sweep of the M937 raw direction. It found no exact
overlap, but alpha `0.15` was a normal-retained near miss: p10 gap and
low-tail fraction moved in the right direction while gap-deficit mean remained
short.

M939 designed boundary-aware training through differentiable interpolation at
alphas `0.125`, `0.150`, and `0.175`.

M940 implemented that objective and preserved the full contract:

```text
reconstructed_rows: 1213 / 1213
joined_target_rows: 122 / 122
training_started: true
boundary_interpolation_used: true
actor_mean_changed: true
fusion_changed: true
response_encoder_changed: false
context_encoder_changed: false
online_gru_changed: false
critic_changed: false
log_std_changed: false
forbidden_parameter_changed: false
```

But M940 still did not produce an admissible alpha:

```text
candidate_alpha_count: 0
strict_candidate_count: 0
low_tail_effect_candidate_count: 0
target_tolerance_candidate_count: 0
normal_safe_low_tail_trend_count: 1
boundary_near_miss_count: 0
result_class: public_base_controlled_fusion_boundary_objective_trust_region_conflict
```

The new boundary is between alpha `0.05` and `0.075`:

```text
alpha 0.05:
  normal_retention_pass: true
  tail_lift_pass: false
  normal_anchor_mse_mean: 0.0000020586
  gap_deficit_mean:       0.0141870732
  low_tail_fraction:      0.3594394028

alpha 0.075:
  normal_retention_pass: false
  tail_lift_pass: true
  normal_anchor_mse_mean: 0.0000040802
  gap_deficit_mean:       0.0128357342
  low_tail_fraction:      0.3066776693
```

Alpha `0.075` misses normal retention only on the mean normal-anchor MSE
threshold:

```text
threshold: 0.0000040000
observed:  0.0000040802
```

## Supported Claims

The controlled-fusion surface is a real low-tail control lever. It is materially
stronger than actor_mean-only updates, and it can produce tail lift without
unfreezing the response encoder, context encoder, online GRU, critic, or
`log_std`.

The P0 human-view actor contract remains intact across the branch. No evidence
in M936-M940 comes from adding hidden dynamics, slip, TTC, feasibility labels,
path references, or wheel channels.

Boundary-aware interpolation training is implemented correctly enough to test
the hypothesis: the M940 run reports `boundary_interpolation_used: true`, starts
the optimizer, and leaves forbidden checksums unchanged.

M940 is not a no-effect result. It shifted useful low-tail movement into a much
smaller alpha region and improved target-action MSE at the normal-retained
`0.05` point.

## Falsified Claims

The M939 objective did not close the M938 alpha `0.15` near miss as registered.
The trained raw direction is too sharp: by alpha `0.075`, tail lift appears, but
normal retention has already failed.

The current controlled-fusion branch cannot justify exact compatibility, replay,
PPO, or promotion. There is no strict candidate and no registered boundary
near-miss candidate in M940.

The evidence does not justify unfreezing response/context encoders or online GRU.
The current failure is a trust-region geometry problem on the allowed surface,
not a demonstrated lack of representational capacity.

## Failure Taxonomy Summary

Primary classification:

```text
promotion_gate_failure
```

M940 cannot advance because no alpha satisfies the public exact-probe
candidate conditions.

Secondary classification:

```text
objective_overfit
```

The boundary objective improves low-tail/tail-lift quantities outside the normal
retention trust region. It optimizes a useful direction, but the admissible
scale is too small.

Rejected classifications:

```text
contract_violation: false
training_instability: false
seed_fragility: not tested in this branch
private_holdout_contamination: false
```

## Public Gate Overfit Risk

The branch repeatedly uses the same public M912/M919 low-tail and target rows.
That is acceptable for objective/tooling diagnosis, but it is not enough for a
driver or paper-level claim.

If a future micro-alpha audit finds a strict candidate, the next step must still
be exact no-update compatibility and then broader replay/fresh-surface
validation. It must not be promoted directly from these public rows.

## Next Branch Decision

Synthesis decision:

```text
continue
```

Continue the controlled-fusion branch for exactly one no-training micro-alpha
audit of the M940 raw direction. This is justified because the registered alpha
grid has a razor boundary:

```text
0.05:  normal-retained, low-tail trend, no tail lift
0.075: tail lift, barely outside normal retention
```

The next audit should sweep the interval around `0.05` to `0.075` more finely.
It must not train, change actor inputs, run replay, run PPO, or promote.

If the micro-boundary audit finds a strict candidate, route to exact no-update
compatibility design.

If it finds no strict candidate, close this branch before touching encoders or
GRU. The next route should be a new synthesis-backed objective family, not more
controlled-fusion variants on the same public rows.

Next blocker:

```text
m942-v4-public-base-controlled-fusion-micro-boundary-audit
```
