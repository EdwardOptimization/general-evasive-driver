# M678 First-Step-Safe Response-Amplification Audit

## Purpose

M678 audits the failed M677 first-step-safe exact probe and selects the next
design. The core question is whether M677 failed because first-step safety did
not work, or because first-step safety worked but suppressed wrong-history
separation.

This milestone is audit-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## M677 Evidence

M677 was implementation-clean:

```text
rows:                           648
source_count:                   216
residual_head_checkpoint_count: 3
actor_parameters_changed:       false
base_actor_checkpoint_written:  false
ppo_used:                       false
promoted:                       false
```

But the exact gate failed:

```text
actor_coupling_exact_passed: false
passed_seed_count:           0
best_selected_alpha:         0.0
```

## What M677 Fixed

M677 fixed the M674 first-action normal drift failure:

```text
M674 alpha=1.0 first drift p95: 0.0094 - 0.0130
M677 alpha=1.0 first drift p95: 0.0025 - 0.0033
```

So the normal first-step anchor and top-k/p95 pressure worked.

## What M677 Broke

M677 suppressed wrong-history sequence separation:

```text
M674 alpha=1.0 gap mean: 0.0121 - 0.0124
M677 alpha=1.0 gap mean: 0.0036 - 0.0069

M674 alpha=1.0 gap ratio: 4.2+
M677 alpha=1.0 gap ratio: 1.25 - 2.40
```

The new loss solved the safety side of the tradeoff but did not preserve enough
variant-branch pressure.

## Classification

M677 should be classified as:

```text
first_step_safety_positive_wrong_gap_suppressed
```

Secondary labels:

```text
normal_first_drift_fixed
wrong_gap_failure_at_safe_alpha
shared_head_branch_interference
objective_overfit
```

The important new hypothesis is `shared_head_branch_interference`: the same
residual head is asked to output near-zero residuals on normal features and
large residuals on wrong-history features. M677 made the normal constraint
strong enough, but the wrong-history branch did not receive enough independent
pressure to remain separated.

## Rejected Interpretations

Reject:

- `first_step_anchor_failed`: it succeeded.
- `representation_failure`: M674/M671 already show the representation can
  produce gap.
- `PPO_needed`: PPO remains blocked until exact residual objectives are
  coherent.
- `weaken_normal_gate`: the normal gate is the safety constraint, not a nuisance.
- `rerun_M677_with_more_epochs`: the failure is a loss-balance/branch-pressure
  issue, not a routing or convergence issue.

## Next Design Target

M679 should design branch-specific response amplification:

```text
normal branch:
  keep first-step zero anchor and top-k/p95 hinge.

wrong branch:
  strengthen wrong-history first-gap and sequence-gap pressure.

gap losses:
  use stop-gradient / detach on normal prediction so gap pressure moves the
  wrong branch, not the normal branch.

sampling:
  optionally use hard wrong-gap rows where M677 gap is lowest.
```

The goal is not to weaken normal safety. The goal is to make the wrong-history
branch carry the separation under the same safety constraint.

## Decision

```text
first_step_safe_audit_admit_branch_specific_design
```

## Next

```text
m679-branch-specific-response-amplification-design
```
