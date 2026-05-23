# M440 Active-Boundary V2 Residual Design

M440 decides whether the M439 audit justifies another active-boundary residual.
It is design-only: no PPO, no projection, no checkpoint promotion, no threshold
changes, and no actor input/output changes.

## Decision

Active-boundary v2 is worth one implementation/probe cycle, but only if it is
row-specific and trajectory-window based. The M439 evidence rejects another
scalar weight sweep:

- v1 repaired M434 `r0015` and improved recovery retained vs M406 to
  `0.120957`;
- v1 did not make `tail_r0010` proof-safe;
- active lambda `1e14` reduced exact active loss but created normal-branch
  collisions and old-key `34 / 40`.

Therefore v2 must encode the active rows more directly while remaining compact
and training-only.

## V2 Corpus

The v2 corpus should be exported from the M438/M439 active cases:

```text
10004|perturbed|31|31|9.500000|-1.000000|0.800000
10023|perturbed|12|12|11.000000|-0.800000|1.200000
9998|perturbed|25|25|11.000000|-1.000000|1.400000
```

Instead of one active-boundary row per failed compact replay case, export a
small trajectory window around each active source step:

```text
window_offsets = [-6, -4, -2, 0]
```

Use fewer offsets if a requested step is unavailable. Do not export full
rollouts. The goal is to cover the pre-terminal branch behavior that
`tail_r0010` lost, without returning to broad full-trajectory imitation.

Corpus fields:

```text
case_id
source_profile
source_condition
paired_condition
source_step
paired_step
window_step
window_offset
violation_type
branch_role
observation
normal_hidden
wrong_hidden
proof_normal_action
proof_wrong_action
candidate_normal_action
candidate_wrong_action
normal_margin
wrong_history_margin
margin_gap
reference_wrong_history_margin
reference_margin_gap
normal_safety_weight
wrong_safety_weight
gap_weight
row_id
profile_index
```

Training-only metadata includes margins, violation type, and weights. None of
these become actor inputs.

## Row Types

Use explicit row families rather than one scalar active-boundary term.

### Wrong-History Safety Rows

Cases:

```text
10004
9998
```

Failure meaning:

```text
wrong-history branch becomes safe or nearly safe
```

Terms:

```text
L_wrong_pref =
  softplus(logp(candidate_wrong_action | wrong_hidden)
           - logp(proof_wrong_action | wrong_hidden)
           + margin)

L_wrong_collision_side =
  softplus(logp(proof_normal_action | wrong_hidden)
           - logp(proof_wrong_action | wrong_hidden)
           + margin)
```

The first term rejects the failing candidate wrong-history action. The second
term keeps the wrong-history branch away from the normal branch when the
correct proof requires wrong-history failure.

### Gap-Erosion Rows

Case:

```text
10023
```

Failure meaning:

```text
normal and wrong branches both remain successful, but their margin gap erodes
below the compact old-key window.
```

Terms:

```text
L_gap_separation =
  softplus(logp(proof_normal_action | wrong_hidden)
           - logp(proof_normal_action | normal_hidden)
           + margin)

L_gap_wrong_identity =
  softplus(logp(candidate_wrong_action | wrong_hidden)
           - logp(proof_wrong_action | wrong_hidden)
           + margin)
```

Weight these by the observed gap deficit:

```text
gap_weight = max(0, reference_margin_gap - margin_gap)
```

### Normal-Safety Rows

Cases:

```text
all active cases when normal_margin is near zero
all rows from high-weight probes that became normal-branch collisions
```

Term:

```text
L_normal_safety =
  || tanh(pi_mean(normal_hidden)) - proof_normal_action ||^2
```

Weight:

```text
normal_safety_weight =
  max(0, normal_margin_floor - normal_margin)
```

Initial `normal_margin_floor`:

```text
0.0015 for 10004 / 9998
0.0100 for 10023
```

This guard is needed because M439 showed that high active-boundary pressure can
repair exact residuals while making normal rollouts collide.

## Weighting

Do not solve v2 with a larger scalar coefficient alone. Use row-local weights:

```text
wrong_safety_weight = max(1e-4, wrong_history_margin + 1e-4)
gap_weight = max(1e-4, reference_margin_gap - margin_gap)
normal_safety_weight = max(0, normal_margin_floor - normal_margin)
```

Then cap each family before applying the global exact-repair coefficient:

```text
wrong_safety_weight <= 0.002
gap_weight <= 0.002
normal_safety_weight <= 0.002
```

The global coefficient can start at `1e12`, matching the successful M438
`r0015` probe. Do not jump to `1e14` without a normal-safety pass, because
M439 showed it creates normal-branch collisions.

## Gate Order

M441 should implement/export v2 and run a no-update exact repair smoke only.

M442 should be the first no-PPO projection probe:

1. exact M297/M270/old-key no-regression;
2. active-boundary v2 residual tracked and not regressed;
3. M267/M264 first replay `17 / 17`;
4. old-key compact replay `40 / 40`;
5. old-key replay gate pass;
6. M183/M170 first replay `17 / 17`;
7. recovery retained vs M406.

Targets:

```text
minimum useful: > M438 r0015 = 0.120957
strong evidence: >= M427 = 0.174354
primary target: >= 0.20
```

## Stop Conditions

Stop this active-boundary branch if any of these happen:

- v2 only reproduces M438 `r0015` and cannot make a looser profile proof-safe;
- v2 makes `tail_r0010` proof-safe but recovery retained remains at or below
  `0.120957`;
- v2 requires broad full-trajectory imitation over the old-key compact set;
- v2 exact loss improves while old-key normal-success cases drop;
- another scalar coefficient sweep is the only proposed next action.

If stopped, return to a broader recovery/proof objective rather than continuing
to tune active-boundary rows.

## Next Milestone

Admit:

```text
m441-active-boundary-v2-residual-implementation
```

M441 should implement the v2 exporter, loader, exact terms, focused tests, and
no-update smoke. It should not run projection or PPO.
