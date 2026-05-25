# M935 V4 Public Base Policy-Level Trust-Region Branch Synthesis

## Purpose

M935 synthesizes the M929-M934 actor_mean-only policy-level trust-region branch.
The branch was opened after residual-head bridge directions could not satisfy
normal retention and low-tail lift at the same time.

This synthesis is required before any broader actor update. It does not train,
run exact compatibility, run replay, run PPO, or promote.

## Evidence Summary

M929 designed the policy-level route after M927/M928 showed that residual-head
directions had a trust-region conflict.

M930 implemented the conservative actor_mean-only probe:

```text
reconstructed_rows: 1213/1213
joined_target_rows: 122/122
actor_mean_changed: true
non_actor_mean_changed: false
candidate_alpha_count: 0
result_class: public_base_policy_head_trust_region_probe_no_tail_lift
```

M931 audited M930 and noted that the registered alphas only went to `0.100`, so
the raw direction still needed an extended-alpha audit.

M932 audited the saved M930 raw actor_mean direction with no new training:

```text
alpha grid through: 1.0
candidate_alpha_count: 0
tail_lift_rows: 0
normal_retained_tail_lift_rows: 0
result_class: public_base_policy_head_raw_direction_feasibility_no_tail_lift
```

At alpha `1.0`, M932 still passed normal retention and weakly improved low-tail
metrics:

```text
low_tail_fraction: 0.41055 -> 0.39736
gap_deficit_mean:  0.01688 -> 0.01638
```

M933 therefore designed one stronger actor_mean-only low-tail pressure probe.

M934 ran that stronger probe:

```text
reconstructed_rows: 1213/1213
joined_target_rows: 122/122
actor_mean_changed: true
non_actor_mean_changed: false
candidate_alpha_count: 0
strict_candidate_count: 0
low_tail_effect_candidate_count: 0
normal_safe_low_tail_trend_count: 3
result_class: public_base_policy_head_trust_region_probe_trust_region_conflict
```

M934 moved low-tail metrics more strongly. At alpha `0.2`, normal retention and
target loss passed, but tail lift did not:

```text
normal_retention_pass: true
tail_lift_pass: false
target_loss_pass: true
low_tail_fraction: 0.39489
gap_deficit_mean: 0.01620
```

At alpha `1.0`, tail lift passed, but normal retention failed:

```text
normal_retention_pass: false
tail_lift_pass: true
low_tail_fraction: 0.34130
gap_deficit_mean: 0.01327
first_action_drift_from_base_mean: 0.00922
first_action_drift_from_base_p95: 0.02158
```

## Supported Claims

The actor_mean-only tooling is valid:

```text
sample reconstruction is complete;
target joins are complete;
only actor_mean changes;
feature/recurrent encoders, critic, and log_std remain unchanged;
replay, PPO, and promotion stayed blocked.
```

The actor_mean surface has some low-tail leverage:

```text
M932 weakly improves low-tail metrics while normal-safe;
M934 creates stronger low-tail movement;
M934 reaches tail_lift_pass at alpha 1.0.
```

The target-active-set diagnostics were useful:

```text
M934 alpha 0.2 improves target loss and low-tail trend while normal-safe;
M934 alpha 1.0 improves low-tail enough for tail lift but loses normal retention
and target loss.
```

## Falsified Claims

Conservative actor_mean-only training is sufficient:

```text
M930 has candidate_alpha_count=0 and no tail lift.
```

The M930 raw direction only needed larger alpha:

```text
M932 extends to alpha 1.0 and still finds tail_lift_rows=0.
```

Stronger actor_mean-only low-tail pressure is sufficient:

```text
M934 creates tail lift only after normal retention fails.
```

Another immediate actor_mean coefficient variant is justified:

```text
The branch now has both no-tail-lift and trust-region-conflict evidence.
Continuing coefficient search would likely become narrow gate-passing.
```

## Failure Taxonomy Summary

Primary classification:

```text
promotion_gate_failure
```

Reason:

```text
No actor_mean-only checkpoint is admissible toward exact/replay work because
the branch produced no alpha that satisfies normal retention, tail lift, and
target/action diagnostics together.
```

Secondary classification:

```text
objective_overfit
```

Reason:

```text
Increasing low-tail pressure can optimize the low-tail objective, but only by
moving the public proof-surface normal actions outside retention bounds.
```

Not classified as:

```text
contract_violation
reconstruction_blocked
target_join_blocked
training_instability
private_holdout_contamination
```

## Public Gate Overfit Risk

Risk is moderate. All recent experiments use the public M912/M919/M755-derived
rows, not private holdout or broad fresh generalization. This is acceptable for
objective feasibility, but not for promotion or driver-improvement claims.

The synthesis explicitly blocks:

```text
exact compatibility
replay
PPO
promotion
driver improvement claims
```

until a stronger candidate exists and then passes exact-first checks.

## Next Branch Decision

Close the actor_mean-only policy-level trust-region branch.

Open a controlled broader-surface branch:

```text
v4_public_base_controlled_fusion_surface
```

The next branch should still be conservative. It should not unfreeze the
response encoder, context encoder, or GRU immediately. The first design should
consider a controlled surface such as:

```text
actor_mean
response_context_fusion final linear layer
```

Rationale:

```text
actor_mean-only has some low-tail leverage but not enough under normal
retention;
full encoder/GRU updates would be too broad;
the fusion layer is the narrowest place to alter how current recurrent belief
and scene context combine before the policy head.
```

## Decision

Next blocker:

```text
m936-v4-public-base-controlled-fusion-surface-design
```

M936 should be design-only. It must pre-register exactly which additional
parameters may train, how non-updated modules are checksummed, and which
objective/proof gates must pass before any exact compatibility, replay, PPO, or
promotion is considered.
