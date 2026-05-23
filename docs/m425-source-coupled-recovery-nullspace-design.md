# M425 Source-Coupled Recovery Nullspace Design

M425 converts the M424 utility-ceiling diagnosis into an implementable design.
It does not run PPO, promote a checkpoint, lower thresholds, or change actor
inputs.

## Problem

The radius-only path cannot reach the primary utility target:

- M423 `mixed_b` is proof-safe but retains only `0.133154` of M406 recovery
  utility;
- M423 `mixed_c` reaches `0.142650`, but M267 rows `6` and `15` become
  wrong-history successes;
- old-key `10023` can fail even when its own radius remains conservative,
  because loosening M267 rows moves shared actor parameters;
- `mixed_b` step `40` already violates exact old-key surrogate no-regression.

So another radius profile is the wrong control variable. The next residual must
move recovery rows only through directions that do not first-order damage the
hard proof rows.

## Hard Constraints

Treat these as active constraints, not soft utility terms:

```text
C_exact:
  exact M297 no-regression
  exact M270 no-regression
  old-key surrogate no-regression

C_replay_active:
  M267/M264 row 6 wrong-history branch guard
  M267/M264 row 15 wrong-history branch guard
  old-key 10023 guard
  old-key spillover guards 9951 and 9939
```

The M267 hard rows should stay at the `mixed_b` radius `0.00030`, not the
`mixed_c` radius `0.00045`. Old-key `10023` should stay at the conservative
radius `0.00020`.

## Recovery Merit

Keep the M398 recovery signal as a utility objective:

```text
U_recovery =
  old_key_recovery_preferred_loss
+ lambda_wrong * old_key_recovery_wrong_anchor_loss
```

The preferred part pushes normal-history actions toward replay-selected local
recovery targets for `9958|perturbed|39|36` and `10004|perturbed|31|31`.
The wrong-history anchor keeps the rejected branch from becoming safe.

This is still training-only metadata. It does not enter the deployable actor
input.

## Projected Gradient

Replace scalar balancing with a projected recovery direction.

Let `g_u = grad(U_recovery)` and `g_i = grad(C_i)` for each active hard
constraint. A plain recovery step `-g_u` increases constraint `C_i` to first
order when:

```text
dot(g_i, g_u) < 0
```

For every conflicting constraint, remove the component of `g_u` that points
against that guard:

```text
if dot(g_i, g_u) < 0:
    g_u <- g_u - dot(g_u, g_i) / (dot(g_i, g_i) + eps) * g_i
```

Then apply the update direction `-g_u_projected` with the existing exact
lexicographic gates and best-feasible checkpoint selection. This is PCGrad-like
gradient surgery, but used as a feasibility-preserving repair step rather than
as a PPO auxiliary loss.

## Implementation Shape

M426 should add tooling, not run the projection probe yet:

1. Add per-source trajectory guard loss reporting for `TrajectoryActionAnchor`.
   The existing aggregate loss is not enough because M424 showed cross-source
   coupling between M267 rows and old-key `10023`.
2. Add a projected-gradient helper in the exact-repair path:
   - flatten only the selected trainable actor-coupling parameters;
   - compute utility gradient from `old_key_recovery_loss`;
   - compute hard gradients from exact hinges and source-specific guard losses;
   - project conflicting utility-gradient components away from hard gradients;
   - write diagnostics: number of active guards, conflict dot products,
     projected-gradient norm, and utility-gradient retained ratio.
3. Keep default behavior unchanged unless the new option is explicitly enabled.
4. Add deterministic unit tests with tiny tensors:
   - projected update does not increase a conflicting hard loss to first order;
   - non-conflicting hard gradients do not alter the utility gradient;
   - zero utility gradient or zero hard gradient is handled safely.
5. Run a no-update exact repair smoke with the option disabled to prove current
   defaults are unchanged.

## Future Probe

After implementation, M427 should run a no-PPO projection probe. The candidate
selection order must remain:

```text
1. exact M297/M270/old-key no-regression
2. M267/M264 first replay rows 6 and 15 plus full 17/17
3. old-key compact replay with 40/40 accepted
4. M183/M170 first replay 17/17
5. recovery retained vs M406
```

No candidate is promotable unless it reaches proof safety first. A utility gain
without M267 row `6`/`15` and old-key `10023` retention remains rejected.

## Decision

Admit implementation-only milestone:

```text
m426-source-coupled-nullspace-implementation
```
