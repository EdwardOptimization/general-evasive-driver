# M249 Protected-Key Source Gradient Audit

M249 audits whether the protected-key source loss is steerable outside PPO. No
PPO was run and actor inputs are unchanged.

## Setup

Initial checkpoint:

```text
runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
```

Protected-key source:

```text
runs/m231_protected_key_snippet_surface/protected_key_snippets.npz
```

Source-only optimization run:

```text
runs/m249_protected_key_source_actor_coupling_probe
```

Combined exact source evaluation:

```text
runs/m249_protected_key_source_combined_exact_eval
```

## Source-Only Probe

The probe optimized only the protected-key source loss for 80 steps in
`actor_coupling` scope:

```text
steps = 80
learning_rate = 5e-5
batch_size = 1
train_scope = actor_coupling
```

| Policy | Protected-key loss |
| --- | ---: |
| before | 0.035642 |
| after | 0.010868 |

The protected-key source loss is clearly steerable in isolation.

## Combined Source Effects

Exact source-aware evaluation against the combined M232 corpus:

| Policy | Exact M232 | M223 component | Protected-key component |
| --- | ---: | ---: | ---: |
| m239_a500 | 0.244649455 | 0.209007065 | 0.035642387 |
| m249_protected_only | 0.074837572 | 0.063969506 | 0.010868066 |
| m248_raw | 0.244610220 | 0.208957569 | 0.035652645 |

Deltas versus M239:

| Policy | M223 delta | Protected-key delta |
| --- | ---: | ---: |
| m249_protected_only | -0.145037559 | -0.024774321 |
| m248_raw | -0.000049496 | 0.000010258 |

This separates the failure modes:

- the protected-key objective is not broken;
- protected-key optimization is aligned with M223 on the exact source corpus;
- M248 failed because PPO rollout/reward/anchor gradients overwhelmed or
  reversed the protected-key source objective.

## Decision

Do not repeat M248 by only increasing PPO duration. Do not run another
source-balanced PPO before adding a protected-source calibration step.

The bounded next repair is a no-PPO actor-coupling calibration plus
interpolation gate from M239 toward the M249 source-only checkpoint. That can
test whether a small fraction of the source-only update improves exact source
objectives while preserving replay/protected-key/behavior gates.

Next step:

```text
m250-protected-key-source-actor-coupling-calibration
```
