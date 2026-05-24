# M681 Branch-Specific Response-Amplification Audit

## Purpose

M681 audits M680 before another objective change. The key question is whether
branch-specific detached-normal gap pressure failed completely, or whether it
created a new, narrower retention blocker.

This milestone is audit-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## M680 Evidence

M680 was implementation-clean:

```text
rows:                           648
source_count:                   216
branch_specific_gap:            true
residual_head_checkpoint_count: 3
actor_parameters_changed:       false
base_actor_checkpoint_written:  false
ppo_used:                       false
promoted:                       false
```

The exact gate failed:

```text
actor_coupling_exact_passed: false
passed_seed_count:           0
best_selected_alpha:         0.0
```

## What Improved

M680 restored much more wrong-history gap than M677.

At `alpha=1.0`:

```text
M677 gap mean: 0.0036 - 0.0069
M680 gap mean: 0.0082 - 0.0106
```

Seed `6801` at `alpha=1.0` passed the wrong-history side:

```text
gap mean:                 0.010645
gap p10:                  0.007573
gap ratio:                3.704878
wrong target improvement: 0.560882
first drift p95:          0.004210
```

So detached-normal branch-specific pressure is valid signal, not a dead end.

## What Failed

The new blocker is full-sequence normal retention:

```text
normal_delta_l2_mean gate: <= 0.0025
M680 alpha=1.0 values:     0.003608 - 0.004284
```

The first executed normal residual remains safe:

```text
first drift p95: 0.004210 - 0.004569 for seeds 6800-6802 at alpha=1.0
gate:            <= 0.0060
```

So the failure is not first-step safety anymore. It is non-executed tail
residual leakage into the normal branch, which still matters because the exact
sequence objective uses the full residual sequence as a diagnostic and future
receding-horizon plan signal.

## Classification

M680 should be classified as:

```text
branch_specific_gap_partial_normal_sequence_retention_failure
```

Secondary labels:

```text
wrong_gap_partially_restored
first_step_safety_retained
normal_sequence_mean_regression
shared_head_tail_leakage
objective_overfit
```

## Rejected Interpretations

Reject:

- `branch_specific_gap_failed`: seed `6801` passes wrong-history gap metrics.
- `first_step_safety_failed`: first drift p95 remains below the gate.
- `PPO_needed`: exact residual objective is still not coherent enough.
- `weaken_normal_sequence_gate`: the sequence residual is a planned-action
  diagnostic and should remain constrained.
- `promotion_possible`: no seed/alpha passes exact gates.

## Next Design Target

M682 should design a normal-sequence-safe variant of M680:

```text
normal branch:
  keep first-step anchor and top-k/p95 hinge;
  add full-sequence normal mean/p95 hinge.

wrong branch:
  keep detached-normal wrong first/sequence gap pressure;
  keep hard low-gap row pressure.

architecture:
  consider split/gated wrong amplifier so the wrong-pressure path is inactive
  on normal-history features.
```

The most conservative next implementation should first try losses before
changing architecture:

```text
L_normal_sequence_topk_hinge
L_normal_sequence_mean_hinge
```

If that still fails, then a later milestone can introduce a split or gated
amplifier head.

## Decision

```text
branch_specific_audit_admit_normal_sequence_safe_design
```

## Next

```text
m682-normal-sequence-safe-response-amplification-design
```
