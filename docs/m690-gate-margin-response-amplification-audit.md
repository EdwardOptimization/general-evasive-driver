# M690 Gate-Margin Response-Amplification Audit

## Purpose

M690 audits the positive M689 exact diagnostic result before allowing any
closed-loop replay, actor update, PPO, or promotion branch.

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
runs/m689_gate_margin_response_amplification/summary.json
runs/m689_gate_margin_response_amplification/alpha_summary.csv
runs/m689_gate_margin_response_amplification/seed_view_summary.csv
docs/m689-gate-margin-response-amplification-implementation.md
```

## M689 Result

M689 is implementation-clean:

```text
rows:                           648
source_count:                   216
residual_head_checkpoint_count: 3
actor_parameters_changed:       false
base_actor_checkpoint_written:  false
ppo_used:                       false
promoted:                       false
```

It passes the exact actor-coupling diagnostic gate:

```text
actor_coupling_exact_passed: true
passed_seed_count:           3
passed_seeds:                6890, 6891, 6892
best_selected_alpha:         1.0
```

All three selected source-holdout rows satisfy the exact output gates:

| seed | normal mean | gap mean | gap ratio | wrong MSE improvement | first drift p95 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 6890 | 0.001441 | 0.011040 | 3.842495 | 0.782311 | 0.003858 |
| 6891 | 0.001380 | 0.011165 | 3.885905 | 0.795998 | 0.004017 |
| 6892 | 0.001461 | 0.010731 | 3.734864 | 0.791428 | 0.003748 |

## Gate Diagnostic Caveat

The pass is real for the registered exact output gates, but it is not yet a
clean gate-factorization result.

The intended gate margin was:

```text
wrong_gate - normal_gate >= 0.30
```

The observed selected source-holdout margin is much smaller:

```text
wrong_gate_margin_mean: 0.061641 - 0.063130
wrong_gate_margin_p10: about -0.046
```

Normal retention passes because the normal raw amplifier is small, not because
the normal gate is closed:

```text
normal_raw_sequence_l2_mean: 0.003116 - 0.003308
wrong_raw_sequence_l2_mean:  0.020149 - 0.020593
normal_gate_mean:           0.435924 - 0.448252
wrong_gate_mean:            0.532601 - 0.544602
```

So M689 should be interpreted as:

```text
output-level normal retention plus wrong-history amplification pass
```

not as:

```text
clean gate-closed self-identification proof
```

## Claim Boundary

Allowed claim:

```text
The frozen-backbone gated residual head can satisfy the registered exact
source-holdout output gates across 3 seeds while leaving the base actor
unchanged.
```

Forbidden claims:

```text
M689 is a deployable driver.
M689 improves closed-loop behavior.
M689 admits PPO.
M689 proves clean gate-factorized self-identification.
M689 promotes a new actor checkpoint.
```

## Classification

Primary classification:

```text
exact_gate_pass_with_gate_diagnostic_caveat
```

Secondary labels:

```text
implementation_clean
normal_retention_positive
wrong_gap_restored
gate_margin_output_positive
normal_gate_not_closed
diagnostic_only_not_promoted
```

## Decision

Do not:

```text
run PPO
promote a checkpoint
write a base actor checkpoint
change actor observations
weaken exact gates
claim closed-loop behavior improvement
```

Do:

```text
admit a design-only closed-loop replay admission milestone
test whether residual-head output separation has trajectory-level utility
keep proof, behavior, and actor-input gates explicit before any actor update
```

## Next Design Target

M691 should design a no-training closed-loop replay admission gate for the M689
residual heads.

The design should answer:

```text
If the selected M689 residual correction is executed or replayed in short
closed-loop continuations, does it improve wrong-history / boundary risk
without degrading normal-history behavior?
```

It should compare at least:

```text
base actor action
M689 residual-corrected action
zero residual
wrong-history residual
```

and report:

```text
terminal margin / collision / road departure
normal-history retention
wrong-history sensitivity
first-action trust region
source-heldout split
```

PPO and promotion remain blocked until this replay admission gate exists and
passes.

## Decision String

```text
gate_margin_response_amplification_audit_admit_closed_loop_replay_design
```

## Next

```text
m691-gate-margin-closed-loop-replay-design
```
