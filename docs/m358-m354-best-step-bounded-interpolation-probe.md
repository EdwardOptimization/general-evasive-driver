# M358 M354 Best-Step Bounded Interpolation Probe

M358 bounds the M356 best-step repair direction after M357 rejected direct
proof-gate acceptance. It does not run PPO and does not promote a checkpoint.

## Inputs

Base:

```text
runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt
```

Target:

```text
runs/m356_m354_repair_best_step_probe/candidate_checkpoint.pt
```

## Coarse Sweep

Run dirs:

```text
runs/m358_m352_to_m354_best_step_interpolation
runs/m358_m354_best_step_old_key_alpha_targeted_replay
```

The coarse grid found that `alpha=0.0025` already fails old-key neighborhood
replay:

| Alpha | Accepted rows | Policy pass |
| ---: | ---: | --- |
| 0.0000 | 40 / 40 | true |
| 0.0025 | 39 / 40 | false |
| 1.0000 | 25 / 40 | false |

This direction is much steeper than the previous M351 accepted direction.

## Micro Sweep

Run dirs:

```text
runs/m358_m352_to_m354_best_step_micro_interpolation
runs/m358_m354_best_step_old_key_micro_targeted_replay
```

Micro old-key targeted replay:

| Alpha | Policy | Accepted rows | Normal success | Policy pass |
| ---: | --- | ---: | ---: | --- |
| 0.00000 | m358_micro_a000 | 40 / 40 | 40 / 40 | true |
| 0.00025 | m358_micro_a0_00025 | 40 / 40 | 40 / 40 | true |
| 0.00050 | m358_micro_a0_0005 | 39 / 40 | 40 / 40 | false |
| 0.00100 | m358_micro_a001 | 39 / 40 | 40 / 40 | false |
| 0.00150 | m358_micro_a0_0015 | 39 / 40 | 40 / 40 | false |
| 0.00200 | m358_micro_a002 | 39 / 40 | 40 / 40 | false |
| 0.00250 | m358_micro_a0_0025 | 39 / 40 | 40 / 40 | false |

Replayable old-key gate for `alpha=0.00025`:

```text
runs/m358_m354_best_step_old_key_micro_a00025_gate
```

Result:

| Metric | Value |
| --- | ---: |
| accepted regressions | 0 |
| normal-success regressions | 0 |
| gap p10 | -0.000001 |
| gap min | -0.000002 |
| overall pass | true |

Replayable old-key gate for `alpha=0.0005`:

```text
runs/m358_m354_best_step_old_key_micro_a0005_gate
```

Result:

```text
overall_pass = false
candidate_accepted_regressions = 1
```

## Exact Check

Selected checkpoint:

```text
runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
```

Exact eval run:

```text
runs/m358_m354_best_step_alpha00025_exact_eval
```

| Objective | Delta vs M352 | Pass |
| --- | ---: | --- |
| Exact M297 rejected-history preference | -0.000000119 | true |
| Exact M270 source-balanced outcome | -0.000000060 | true |

## Interpretation

M358 finds a nonzero but extremely small safe movement along the M356 best-step
repair direction:

```text
selected alpha = 0.00025
first failing alpha = 0.0005
```

This is positive only as bounded direction evidence. It is not promotion
evidence, and it shows the M356 direction remains highly constrained by
old-key neighborhood proof.

## Decision

Admit:

```text
m359-m354-best-step-micro-alpha-proof-gate
```

Decision:

```text
admit_m359_m354_best_step_micro_alpha_probe
```
