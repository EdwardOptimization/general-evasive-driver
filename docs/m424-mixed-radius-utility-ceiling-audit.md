# M424 Mixed-Radius Utility Ceiling Audit

M424 audits the M420/M423 radius-only path. It does not run PPO, promote a
checkpoint, lower thresholds, or change actor inputs.

## Summary

The radius-only path has reached a utility ceiling. It can improve the
proof-safe recovery-retention ratio from M420 conservative `0.115403` to
M423 `mixed_b` `0.133154`, but the next useful loosening reopens active proof
rows before reaching the primary `0.20` utility threshold.

| Candidate | Radius change | Proof result | Recovery retained vs M406 |
| --- | --- | --- | ---: |
| M420 conservative | tight all active rows | pass | `0.115403` |
| M423 `mixed_a` | medium except tight `10023` | pass | `0.126033` |
| M423 `mixed_b` | `mixed_a` plus loose `10004` | pass | `0.133154` |
| M420 medium | medium all active rows | old-key `39 / 40` | `0.143419` |
| M423 `mixed_c` | `mixed_b` plus loose M267 rows `6`/`15` | M267 `15 / 17`, old-key `39 / 40` | `0.142650` |

The best proof-safe candidate is `mixed_b`, but it is still only two thirds of
the required `0.20` recovery-retention target.

## Binding Rows

M267 rows `6` and `15` are hard active constraints. `mixed_b` keeps them barely
negative under wrong-history rollout, while `mixed_c` crosses both positive:

| Row | `mixed_b` wrong-history margin | `mixed_c` wrong-history margin |
| --- | ---: | ---: |
| M267 row `6` | `-0.000035874` | `+0.000032680` |
| M267 row `15` | `-0.000033767` | `+0.000028111` |

This means the M267 radius cannot simply be loosened from `0.00030` to
`0.00045`. The extra utility is real but it comes by making wrong-history
branches safe, which destroys the self-identification proof.

Old-key case `10023|perturbed|12|12` is also a hard guard:

| Candidate | `10023` accepted | Normal margin | Wrong-history margin | Gap |
| --- | --- | ---: | ---: | ---: |
| M420 medium | false | `0.049220713` | `0.047232692` | `0.001988021` |
| M420 conservative | true | `0.049110575` | `0.047107760` | `0.002002815` |
| `mixed_a` | true | `0.049127080` | `0.047125280` | `0.002001800` |
| `mixed_b` | true | `0.049159904` | `0.047158830` | `0.002001074` |
| `mixed_c` | false | `0.049147864` | `0.047149970` | `0.001997895` |

`mixed_c` keeps `10023` itself at the tight conservative radius, yet `10023`
still fails. So this is not a single-row radius mistake. Loosening M267 rows
changes the shared actor enough to affect old-key `10023`.

## Exact Feasibility Boundary

`mixed_b` is already at an exact old-key surrogate boundary. Its selected
candidate is step `39`; step `40` has:

```text
old_key_surrogate_delta_vs_base = +0.0000038147
exact_lexicographic_pass = false
```

So even before replay, the exact full-corpus gate is stopping the direction.
Another radius profile can move this boundary slightly, but the active set is
now source-coupled rather than profile-local.

## Recovery Rows

The recovery targets remain useful but are not reachable enough under the
current radius-only formulation:

| Case | M420 conservative normal margin | M423 `mixed_b` normal margin | M423 `mixed_c` normal margin |
| --- | ---: | ---: | ---: |
| `9958|perturbed|39|36` | `0.001115193` | `0.001267324` | `0.001439878` |
| `10004|perturbed|31|31` | `0.000525306` | `0.000578623` | `0.000593007` |

The useful movement is toward more normal-branch slack on these recovery rows.
But the proof failures appear before that movement reaches the primary utility
target.

## Interpretation

M424 classifies this as a radius-only utility ceiling:

- `10023` must remain tightly guarded;
- M267 rows `6` and `15` must remain near the `0.00030` radius;
- loosening M267 rows gives utility but washes out wrong-history proof;
- even with tight `10023`, the old-key guard can fail through shared actor
  coupling;
- `mixed_b` is already bounded by exact old-key surrogate feasibility at the
  next optimizer step.

The next change should not be another per-source radius tweak. The residual
needs to express recovery utility while treating M267 rows `6` and `15` plus
old-key `10023` as hard active constraints.

## Decision

Stop the radius-only path and admit a design milestone:

```text
m425-source-coupled-recovery-nullspace-design
```
