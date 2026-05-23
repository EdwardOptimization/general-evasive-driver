# M436 Old-Key Active-Boundary Residual Design

M436 designs the next residual after M435. It does not train, promote a
checkpoint, lower thresholds, or change actor inputs.

## Why Radius Tuning Stops Here

M434/M435 found the selective radius ceiling:

- `r0010` is proof-safe but only retains `0.103529` of M406 recovery utility;
- `r0015` fails `10023` gap erosion;
- `r0020` fails `10004` wrong-history safety and `10023`;
- terminal-only profiles fail `10004`/`10023` and expose `9998`.

This means the active proof boundary is multi-key. Another source radius sweep
will likely move the same boundary around without reaching the `0.20` utility
target.

## Active-Boundary Corpus

M437 should export a compact corpus from the M434 artifacts with one row per
active branch/step sample:

```text
case_id
source_profile
branch
observation
normal_hidden
wrong_hidden
proof_normal_action
proof_wrong_action
candidate_normal_action
candidate_wrong_action
normal_margin
wrong_margin
margin_gap
violation_type
weight
```

Initial cases:

| Case | Source | Violation type |
| --- | --- | --- |
| `10023|perturbed|12|12` | `r0015`, `r0020`, tail profiles | gap erosion |
| `10004|perturbed|31|31` | `r0020`, tail profiles | wrong-history became safe |
| `9998|perturbed|25|25` | `tail_r0010` | spillover wrong-history became nearly safe |

Use M400 or proof-safe `r0010` as the proof action source. Use the failing
profile action only as a rejected/negative action, not as an imitation target.

## Loss Shape

The residual should be preference-based, not broad full-trajectory imitation.

For wrong-history safety rows where the wrong branch becomes safe:

```text
L_wrong =
  softplus(logp(candidate_wrong_action | wrong_hidden)
           - logp(proof_wrong_action | wrong_hidden)
           + margin)
```

For gap-erosion rows such as `10023`, preserve branch separation:

```text
L_gap =
  softplus(logp(proof_normal_action | wrong_hidden)
           - logp(proof_normal_action | normal_hidden)
           + margin)
  +
  softplus(logp(candidate_wrong_action | wrong_hidden)
           - logp(proof_wrong_action | wrong_hidden)
           + margin)
```

For normal-branch collision rows, only then add a local normal safety anchor:

```text
L_normal =
  || pi(normal_hidden) - proof_normal_action ||^2
```

The active-boundary corpus should weight rows by observed violation:

```text
wrong_safe_weight = max(0, wrong_margin + epsilon)
gap_weight = max(0, gap_floor - margin_gap)
normal_collision_weight = max(0, -normal_margin)
```

This keeps the residual tied to closed-loop proof failures while remaining a
training-time objective. None of these fields become actor inputs.

## Integration

M437 should implement:

- an active-boundary corpus exporter from old-key replay `guard_results.csv`
  plus checkpoint actions;
- a loader/dataclass for the corpus;
- exact repair loss terms for `wrong`, `gap`, and optional `normal` rows;
- a no-update exact repair smoke.

M438 should then run a no-PPO projection probe. Gate order remains:

1. exact M297/M270/old-key no-regression;
2. active-boundary exact residual no-regression/improvement;
3. M267/M264 first replay `17 / 17`;
4. old-key compact `40 / 40`;
5. M183/M170 first replay `17 / 17`;
6. recovery retained vs M406.

## Decision

Admit:

```text
m437-active-boundary-residual-implementation
```

Do not run PPO before this residual has a no-update smoke and a no-PPO proof
probe.
