# M444 Proof-Utility Generalization Audit

M444 runs a non-promotion broad benchmark to test whether proof-rejected
high-recovery candidates show real value on a fresh randomized scenario
distribution. No PPO was run, no checkpoint was promoted, and actor
inputs/outputs were unchanged.

Benchmark run:

```text
runs/m444_proof_utility_generalization_seed9600
```

Policies:

```text
heuristic
m399_base
m434_r0010
m438_r0015
m427_high_utility
m442_tail_v2
```

The benchmark uses:

```text
env config = configs/m121_human_view_zero_obstacle_relvel.json
episodes   = 160
seed       = 9600
```

## Policy Summary

| Policy | Success | Collision | Return | Mean margin | Min margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | `0.3125` | `0.68125` | `42.229248` | `0.195925` | `-0.296268` |
| M399 base | `0.8625` | `0.13750` | `68.263736` | `1.771655` | `-0.257598` |
| M427 high-utility rejected | `0.8625` | `0.13750` | `68.257708` | `1.771776` | `-0.259425` |
| M434 `r0010` proof-safe | `0.8625` | `0.13750` | `68.273303` | `1.771805` | `-0.258343` |
| M438 `r0015` proof-safe | `0.8625` | `0.13750` | `68.272791` | `1.771780` | `-0.258579` |
| M442 tail v2 rejected | `0.8625` | `0.13750` | `68.260798` | `1.771809` | `-0.258514` |

## Deltas Vs Base

| Policy | Success delta | Collision delta | Return delta | Mean-margin delta | Min-margin delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| M427 high-utility rejected | `0.0` | `0.0` | `-0.006028` | `0.000121` | `-0.001828` |
| M434 `r0010` proof-safe | `0.0` | `0.0` | `0.009568` | `0.000150` | `-0.000745` |
| M438 `r0015` proof-safe | `0.0` | `0.0` | `0.009055` | `0.000125` | `-0.000981` |
| M442 tail v2 rejected | `0.0` | `0.0` | `-0.002938` | `0.000154` | `-0.000916` |

There are zero per-seed success differences between M399 and any checkpoint
candidate:

| Candidate | Per-seed success differences vs M399 |
| --- | ---: |
| M427 high-utility rejected | `0` |
| M434 `r0010` proof-safe | `0` |
| M438 `r0015` proof-safe | `0` |
| M442 tail v2 rejected | `0` |

## Bucket Checks

By obstacle label, all checkpoint policies match the base success rates:

| Label | Episodes | M399 success | Candidate success range |
| --- | ---: | ---: | ---: |
| `aes_feasible` | `28` | `1.000000` | `1.000000` to `1.000000` |
| `drift_required` | `81` | `0.938272` | `0.938272` to `0.938272` |
| `unavoidable` | `51` | `0.666667` | `0.666667` to `0.666667` |

By initial-mu bucket, all checkpoint policies also match the base success
rates:

| Initial mu bucket | Episodes | M399 success | Candidate success range |
| --- | ---: | ---: | ---: |
| `low` | `59` | `0.949153` | `0.949153` to `0.949153` |
| `medium` | `101` | `0.811881` | `0.811881` to `0.811881` |

## Interpretation

The broad benchmark does not support the claim that the proof-rejected
high-recovery candidate is better on fresh randomized scenarios.

M427 retained more of the M406 old-key recovery direction than the proof-safe
active-boundary candidates, but that does not show up as higher success,
lower collision rate, or a meaningful return improvement in this 160-episode
fresh benchmark. The differences that remain are small margin/return shifts,
not driver-level behavior changes.

This means the recent proof/utility branch should not continue optimizing
M406-style recovery retained as a standalone proxy. It may still be useful as a
diagnostic, but it is not yet evidence of broad driver improvement.

The benchmark is also too coarse to define the next objective by itself:
aggregate success is saturated enough that all checkpoint candidates tie. The
next useful step is to mine fresh scenarios where policies actually diverge in
closed-loop outcome, margin, or action response, then decide whether those
divergences correspond to real self-identification behavior.

## Decision

M444 passes as a diagnostic audit:

- benchmark artifacts were produced;
- no checkpoint is promoted;
- proof-rejected high-recovery candidates do not beat M399 on broad success;
- M406 recovery retained is not accepted as a broad performance proxy;
- the next branch should find fresh policy-difference scenarios before more
  objective design.

Admit:

```text
m445-fresh-policy-difference-miner-design
```

M445 should design a source-diverse miner for fresh near-boundary scenarios
where M399, proof-safe candidates, and proof-rejected high-utility candidates
actually differ. That miner should become the basis for the next generalization
surface, not another active-boundary scalar sweep.
