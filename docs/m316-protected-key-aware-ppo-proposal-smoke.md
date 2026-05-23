# M316 Protected-Key-Aware PPO Proposal Smoke

M316 runs one fresh smoke-scale PPO proposal from the M314 public-gate base and
applies the pre-registered acceptance stack. Actor inputs are unchanged.

## Raw PPO Proposal

Initial checkpoint:

```text
runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt
```

Raw PPO checkpoint:

```text
runs/ppo_m316_protected_key_aware_proposal_smoke_seed5235/checkpoint.pt
```

Smoke metrics:

| Metric | Value |
| --- | ---: |
| rollout_return_mean | 65.411459 |
| reward_mean | 1.053202 |
| training termination_rate | 0.230769 |
| eval return_mean | 74.498377 |
| eval termination_rate | 0.000000 |
| rejected_history_preference_loss_mean | 1.071393 |

Raw PPO is only a proposal. It regresses exact full-corpus objectives versus
M314:

| Objective | Raw delta vs M314 |
| --- | ---: |
| Exact M297 rejected-history preference | +0.000779867 |
| Exact M270 source-balanced outcome | +0.000490844 |

## Exact Repair

Exact repair run:

```text
runs/m316_exact_repair_from_raw_s40_seed10096
```

Repaired candidate:

```text
runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
```

Exact repair recovers the proposal under M297/M270:

| Objective | Repaired delta vs M314 |
| --- | ---: |
| Exact M297 rejected-history preference | -0.000117064 |
| Exact M270 source-balanced outcome | -0.000076056 |

## Protected-Key-Bounded Interpolation

Interpolation run:

```text
runs/m316_m314_to_repaired_protected_key_bounded_interpolation
```

Exact line search passes for every tested alpha through `1.0`, but protected
key `9944|perturbed|28|28` is the active constraint.

| Alpha | Exact M297 delta | Exact M270 delta | Protected key pass | Normal margin |
| ---: | ---: | ---: | --- | ---: |
| 0.0000 | +0.000000000 | +0.000000000 | true | 0.199976 |
| 0.0025 | -0.000000477 | -0.000000298 | true | 0.199995 |
| 0.0050 | -0.000000715 | -0.000000417 | false | 0.200015 |
| 0.0100 | -0.000001311 | -0.000000834 | false | 0.200053 |
| 1.0000 | -0.000117064 | -0.000076056 | false | 0.207388 |

Selected alpha:

```text
0.0025
```

Selected checkpoint:

```text
runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt
```

Protected key at selected alpha:

| Policy | Pass | Accepted cases | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: | ---: |
| m316_a0_0025 | true | 1 / 1 | 0.199995 | 0.100123 | 0.099873 |

## First Replay Gates

### M183/M170

Run dir:

```text
runs/m316_a0_0025_m183_m170_first_replay
```

| Metric | Value |
| --- | ---: |
| Normal success | 1.000000 |
| Wrong-history success | 0.000000 |
| Success drops retained | 17 / 17 |
| Normal margin mean delta | +0.000000580 |
| Margin gap mean delta | +0.000000072 |
| Gate pass | true |

### M267/M264

Run dir:

```text
runs/m316_a0_0025_m267_m264_first_replay
```

| Metric | Value |
| --- | ---: |
| Normal success | 1.000000 |
| Wrong-history success | 0.000000 |
| Success drops retained | 17 / 17 |
| Normal margin mean delta | +0.000000523 |
| Margin gap mean delta | +0.000000198 |
| Gate pass | true |

## Interpretation

M316 is a qualified first-gate positive. The raw PPO proposal contains useful
movement after exact repair, but the M314 protected key is nearly saturated, so
the accepted trust-region step collapses to `alpha=0.0025`.

This should not be promoted directly. The correct next step is a separate full
public gate for the selected tiny-alpha candidate.

## Decision

Admit:

```text
m317-full-public-gate-for-m316-a0-0025
```

Decision:

```text
admit_m317_full_public_gate_for_m316_a0_0025
```
