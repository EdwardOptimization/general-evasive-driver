# M684 Normal-Sequence-Safe Response-Amplification Audit

## Purpose

M684 audits the failed M683 exact probe before choosing the next response
amplification branch.

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
runs/m683_normal_sequence_safe_response_amplification/summary.json
runs/m683_normal_sequence_safe_response_amplification/alpha_summary.csv
docs/m683-normal-sequence-safe-response-amplification-implementation.md
```

## M683 Result

M683 is implementation-clean:

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

## Evidence

M683 improved normal full-sequence retention relative to M680:

```text
M680 best alpha=1.0 normal mean: 0.003753
M683 best alpha=1.0 normal mean: 0.002769
```

It also kept first-step drift inside the exact gate:

```text
M683 alpha=1.0 first drift p95 range: 0.004269 - 0.004284
gate:                                 <= 0.0060
```

But the normal-sequence anchor suppressed wrong-history amplification:

```text
M680 best alpha=1.0 gap mean:              0.010645
M680 best alpha=1.0 gap ratio:             3.704878
M680 best alpha=1.0 wrong MSE improvement: 0.560882

M683 best alpha=1.0 gap mean:              0.008320
M683 best alpha=1.0 gap ratio:             2.895718
M683 best alpha=1.0 wrong MSE improvement: 0.438964
```

M683 also did not fully satisfy normal mean at `alpha=1.0`:

```text
M683 alpha=1.0 normal mean range: 0.002769 - 0.002958
gate:                            <= 0.0025
```

Lower alphas satisfy normal retention but reduce wrong-history gap far below
threshold.

## Interpretation

M680 and M683 now bracket the conflict:

```text
M680:
  detached-normal wrong pressure restores gap,
  but normal full-sequence residual is too large.

M683:
  normal full-sequence pressure reduces normal residual,
  but wrong-history gap falls below threshold and normal mean remains slightly high.
```

This is no longer a first-step safety blocker. It is also not a missing
wrong-history signal blocker, because M680 showed the wrong branch can be
amplified.

The likely blocker is the shared residual-head objective:

```text
one residual head must be almost zero on normal features
and large on closely related wrong-history features
using only scalar loss balancing
```

Pushing the scalar normal loss harder should further suppress wrong-history
gap. Pushing the scalar wrong loss harder should repeat M680's normal sequence
failure. A small coefficient grid could refine the boundary, but it is unlikely
to change the structural tradeoff.

## Classification

Primary classification:

```text
wrong_gap_suppressed_by_normal_sequence_anchor
```

Secondary labels:

```text
implementation_clean
objective_overfit
shared_head_capacity_conflict_possible
normal_sequence_retention_improved
wrong_history_gap_regressed
```

## Decision

The next design should not:

```text
weaken exact normal gates
run PPO
promote a checkpoint
change actor inputs
only increase scalar auxiliary weights
```

The next design should introduce a structural way to keep normal-history
residuals inactive while allowing wrong-history residuals to amplify:

```text
split/gated residual response amplifier
```

The design should stay diagnostic and frozen-backbone:

```text
frozen BC5660 actor
fused_plus_next_hidden features
train only residual head/gate parameters
execute only first residual in alpha ladder
no base actor checkpoint
no PPO
no promotion
```

## Next Design Target

M685 should design a gated/split head such as:

```text
residual_sequence = gate(feature) * amplifier(feature)
```

with training pressure:

```text
normal residual zero
normal gate near zero
wrong residual target
wrong gate open enough to reach target gap
normal first-step safety
normal full-sequence mean/top-k safety
detached-normal wrong-history gap
hard low-gap wrong rows
```

The key test is whether separating "when to activate" from "what residual to
emit" can avoid the M680/M683 scalar-loss tradeoff.

## Decision String

```text
normal_sequence_safe_audit_admit_split_gated_design
```

## Next

```text
m685-split-gated-response-amplification-design
```
