# M405 Recovery-Aware Exact Projection Design

M405 designs the next no-PPO repair step after M404 showed that the
recovery-heavy direction conflicts broadly with exact M297/M270. This milestone
does not run PPO, promote a checkpoint, lower thresholds, or change actor
inputs.

## Problem

M403 showed a scalar recovery-weight sweep is not enough:

```text
low recovery weights: exact-safe, but move away from the M398 recovery target
high recovery weights: move toward recovery and improve old-key, but violate exact M297/M270
```

M404 showed why:

```text
M297: 17 / 17 rows regress under recovery-heavy alpha 0.025
M270: 99 / 99 rows regress under recovery-heavy alpha 0.025
```

So this is not a single-row active-set issue. The recovery direction is outside
the current exact feasible tangent.

## Design Principle

The next repair must be lexicographic:

```text
Level 1: exact M297 no-regression
Level 2: exact M270 no-regression
Level 3: old-key surrogate no-regression
Level 4: retain M267/M264 and old-key closed-loop proof gates
Level 5: maximize retained movement toward M398 recovery target
```

Recovery movement is not allowed to buy exact regression. It is a secondary
merit objective only after exact feasibility is restored.

## Projection Recipe

Use existing `exact_post_ppo_repair` infrastructure first, before adding new
code.

Candidate raw directions:

| Raw | Reason |
| --- | --- |
| `runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt` | small recovery-heavy movement; old-key targeted replay passes; exact fails mildly |
| `runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_6.pt` | stronger recovery/old-key movement; old-key compact passes; M267 fails, used only as stress |

Projection mode:

```text
start_mode: repair_from_raw
steps: 20 to 40
train_scope: actor_coupling
exact lambdas: M297/M270/old-key remain very large
lambda_param_raw: positive, to retain useful raw movement
lambda_old_key_recovery: high enough to keep recovery direction visible
selection_policy: best_feasible
```

Acceptance is not based on training loss. A candidate is useful only if:

```text
exact M297/M270/old-key no-regression passes
distance_to_M398_recovery_action on 9958 decreases versus M400 base
cumulative old-key compact replay passes
M267/M264 first replay retains 17 / 17 success drops
M183/M170 first replay passes if the first two proof gates pass
```

If projection returns the base or erases recovery movement, classify as:

```text
projection_collapses_to_base
```

If projection restores exact but fails replay:

```text
exact_feasible_replay_infeasible
```

If projection keeps recovery movement but exact remains violated:

```text
exact_restoration_failed
```

## Why This Is Better Than Another Weight Sweep

A weight sweep optimizes a scalarized loss. M404 showed the exact terms are a
broad active constraint, so scalarization either:

```text
lets exact dominate and ignores recovery
or lets recovery dominate and violates exact
```

Projection treats the recovery-heavy update as a proposal, then asks whether any
nearby point can satisfy exact feasibility while retaining some recovery
movement. This is closer to a constrained optimizer workflow.

## Decision

Admit a no-PPO projection probe:

```text
m406-recovery-aware-exact-projection-probe
```
