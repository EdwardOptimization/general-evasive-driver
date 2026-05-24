# M687 Split-Gated Response-Amplification Audit

## Purpose

M687 audits the failed M686 split/gated response-amplification exact probe.

This milestone is audit-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
no actor-input change
```

## Inputs Audited

```text
runs/m686_split_gated_response_amplification/summary.json
runs/m686_split_gated_response_amplification/alpha_summary.csv
runs/m686_split_gated_response_amplification/seed_view_summary.csv
runs/m686_split_gated_response_amplification/train_metrics.csv
docs/m686-split-gated-response-amplification-implementation.md
```

## M686 Result

M686 is implementation-clean:

```text
rows:                           648
source_count:                   216
head_type:                      gated
max_residual:                   0.04
actor_parameters_changed:       false
base_actor_checkpoint_written:  false
ppo_used:                       false
promoted:                       false
```

Exact gate failed:

```text
actor_coupling_exact_passed: false
passed_seed_count:           0
best_selected_alpha:         0.0
```

## Evidence

M686 strongly improves normal retention:

```text
alpha=1.0 normal_delta_l2_mean: 0.001097 - 0.001159
gate:                           <= 0.0025

alpha=1.0 normal_delta_l2_p95:  0.002386 - 0.002562
gate:                           <= 0.0060
```

But wrong-history gap remains below threshold:

```text
alpha=1.0 gap mean:  0.006386 - 0.006416
gate:                >= 0.010

alpha=1.0 gap ratio: 2.222601 - 2.233034
gate:                >= 3.0
```

Gate diagnostics identify the failure:

```text
normal_gate_mean: 0.097540 - 0.098755
wrong_gate_mean:  0.102354 - 0.104949
wrong_gate_target: 0.50
```

The wrong gate is not opening; it is only about `0.004` to `0.006` above the
normal gate.

This is not bounded-amplifier capacity failure:

```text
wrong_raw_sequence_l2_mean: 0.060179 - 0.062896
normal_raw_sequence_l2_mean: 0.010694 - 0.011445
```

The raw wrong amplifier is large. The gate attenuates it to roughly `10%`.

## Classification

Primary classification:

```text
gate_collapse
```

Secondary labels:

```text
normal_retention_strong_positive
wrong_gate_open_failure
wrong_gap_below_threshold
not_amplifier_capacity_failure
implementation_clean
```

## Interpretation

M686 proves the split/gated structure can keep normal residuals inactive. The
remaining issue is that the gate objective does not force wrong-history features
to open relative to normal features.

The current wrong gate-open coefficient is too weak:

```text
wrong_gate_open_coef: 0.25
wrong_gate_open_hinge: about 0.156 - 0.159 at final epoch
```

This leaves a large unsatisfied residual in the loss rather than a passable
gate split.

The next branch should add explicit gate separation instead of only asking the
wrong gate to approach an absolute target:

```text
gate_wrong - stop_gradient(gate_normal) >= margin
```

and hard pressure on the lowest wrong gates or lowest wrong-history gaps.

## Decision

Do not:

```text
weaken normal retention gates
remove the gate
run PPO
promote a checkpoint
change actor inputs
```

Do:

```text
add detached-normal wrong-vs-normal gate margin;
increase wrong gate-open pressure;
add hard low-gate wrong rows;
keep normal gate close losses;
keep exact alpha ladder gates unchanged.
```

## Next Design Target

M688 should design:

```text
gate-margin response amplification
```

with:

```text
L_wrong_gate_margin =
  weighted_mean(max(0, margin - (gate_wrong - detach(gate_normal)))^2)

L_wrong_gate_hard =
  top-k lowest wrong gates or lowest output gaps with stronger open pressure
```

Initial design direction:

```text
wrong_gate_open_coef:      2.0
wrong_gate_margin_coef:    2.0
wrong_gate_margin:         0.30
wrong_gate_hard_coef:      1.0
wrong_gate_hard_fraction:  0.25
normal_gate_coef:          keep 1.0
normal_gate_threshold:     keep 0.10
```

This tests whether the gated head can open wrong-history features without
giving up the normal retention gains.

## Decision String

```text
split_gated_audit_admit_gate_margin_design
```

## Next

```text
m688-gate-margin-response-amplification-design
```
