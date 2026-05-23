# M359 M354 Best-Step Micro-Alpha Proof Gate

M359 evaluates the M358 selected micro-alpha candidate on source-diverse and
first replay proof gates. It does not run PPO and does not promote a checkpoint.

## Candidate

```text
runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
```

M358 already established:

| Gate | Result |
| --- | --- |
| Exact M297/M270 | pass |
| Old-key neighborhood | pass |
| First failing old-key alpha | 0.0005 |

## Source-Diverse Protected Gate

Run dir:

```text
runs/m359_m354_best_step_micro_alpha_source_diverse_protected_gate
```

Result:

```text
5 / 5 replay gates pass
```

| Replay gate | Rows | Candidate drops | Gate |
| --- | ---: | ---: | --- |
| current_m333_surface | 17 | 17 | pass |
| m328_continuity_surface | 17 | 17 | pass |
| m325_continuity_surface | 17 | 17 | pass |
| m317_continuity_surface | 17 | 17 | pass |
| m314_continuity_surface | 17 | 17 | pass |

## First Replay Gates

| Surface | Rows | Success drops retained | Gate |
| --- | ---: | ---: | --- |
| M183/M170 | 17 | 17 / 17 | pass |
| M267/M264 | 17 | 17 / 17 | pass |

Run dirs:

```text
runs/m359_m354_best_step_micro_alpha_m183_m170_first_replay
runs/m359_m354_best_step_micro_alpha_m267_m264_first_replay
```

## Interpretation

M359 is positive as a proof-gate probe. The selected `alpha=0.00025` candidate
preserves exact, old-key neighborhood, source-diverse, and first replay proof
gates.

The result is still heavily qualified:

```text
accepted alpha = 0.00025
first failing alpha = 0.0005
```

So the M356 direction is only usable in a very small trust region.

## Decision

Admit:

```text
m360-full-public-gate-for-m358-a00025
```

Decision:

```text
admit_m360_full_public_gate_for_m354_micro_alpha
```
