# M675 Response-Amplification Actor-Coupling Audit

## Purpose

M675 audits the failed M674 actor-coupling exact gate. The goal is to separate
an implementation failure from a useful negative result and choose the next
highest-leverage design.

This milestone is audit-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## M674 Evidence

M674 was implementation-clean:

```text
rows:                           648
source_count:                   216
residual_head_checkpoint_count: 3
actor_parameters_changed:       false
base_actor_checkpoint_written:  false
ppo_used:                       false
promoted:                       false
```

But the exact actor-coupling gate failed:

```text
actor_coupling_exact_passed: false
passed_seed_count:           0
best_selected_alpha:         0.0
```

## Failure Shape

The alpha ladder exposes a clean constraint conflict:

```text
alpha=1.0:
  wrong-history sequence gap passes;
  first-action normal drift p95 fails.

alpha=0.5:
  first-action normal drift is mostly safe;
  wrong-history sequence gap and ratio fail.
```

Representative source-heldout rows:

| seed | alpha | normal mean | gap mean | gap ratio | first drift p95 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 6740 | 0.50 | 0.001197 | 0.006059 | 2.108998 | 0.004860 |
| 6740 | 1.00 | 0.002394 | 0.012119 | 4.217997 | 0.009719 |
| 6741 | 0.50 | 0.001329 | 0.006206 | 2.160026 | 0.004702 |
| 6741 | 1.00 | 0.002657 | 0.012412 | 4.320051 | 0.009403 |
| 6742 | 0.50 | 0.001349 | 0.006094 | 2.121143 | 0.006481 |
| 6742 | 1.00 | 0.002699 | 0.012189 | 4.242287 | 0.012962 |

The M674 head can reproduce the M671-style wrong-history sequence separation.
It cannot execute the first residual safely under the current normal-drift gate.

## Classification

M674 should be classified as:

```text
first_action_drift_vs_sequence_gap_conflict
```

Process labels:

```text
implementation_clean
exact_gate_failure
normal_retention_failure_at_high_alpha
wrong_gap_failure_at_low_alpha
objective_overfit
```

`objective_overfit` is appropriate because the sequence-level objective
optimizes the diagnostic residual but does not explicitly constrain the
executed first residual enough.

## Rejected Interpretations

Reject:

- `representation_failure`: alpha `1.0` has enough sequence gap.
- `actor_input_contract_failure`: actor inputs did not change.
- `PPO_needed`: PPO would only add more moving parts before the exact residual
  constraint is fixed.
- `promotion_possible`: no candidate passed exact gates.
- `weaken_normal_drift_gate`: the failure is precisely about executable action
  safety, so weakening it would hide the blocker.

## Next Design Target

M676 should design a first-step-safe residual objective, not another generic
sequence head.

The key change should be:

```text
make the executed first residual a first-class training objective and gate.
```

Required design elements:

```text
L_normal_first_anchor:
  strong penalty on normal hidden first residual.

L_normal_first_topk:
  approximate p95 / worst-row penalty so a few rows cannot violate the gate.

L_wrong_sequence_target:
  preserve the M671 wrong-history sequence target.

L_wrong_first_min_gap:
  encourage useful wrong-history first residual without exceeding trust region.

alpha ladder:
  retained, but expected to pass at larger alpha only if first residual is safe.
```

M676 should keep:

```text
frozen BC5660 backbone
fused_plus_next_hidden feature view
no PPO
no promotion
no actor input change
exact metrics before replay
```

## Decision

```text
response_amplification_actor_coupling_audit_admit_first_step_safe_design
```

## Next

```text
m676-first-step-safe-response-amplification-design
```
