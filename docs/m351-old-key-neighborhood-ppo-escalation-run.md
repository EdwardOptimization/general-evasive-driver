# M351 Old-Key Neighborhood PPO Escalation Run

M351 runs the short PPO proposal registered by M350. The PPO checkpoint is
proposal-only. M351 does not promote a new public base.

## Raw PPO

Base:

```text
runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt
```

Config:

```text
configs/ppo_m351_old_key_neighborhood_escalation.json
```

Raw PPO run:

```text
runs/ppo_m351_old_key_neighborhood_escalation_seed5239
```

Raw PPO metrics:

| Metric | Value |
| --- | ---: |
| rollout_return_mean | 75.00 |
| reward_mean | 1.070 |
| eval return_mean | 51.942395 |
| eval termination_rate | 0.200000 |

The raw PPO checkpoint is not promotable.

## Exact Repair

Exact repair run:

```text
runs/m351_exact_repair_from_raw_s40_seed10101
```

Repaired endpoint:

```text
runs/m351_exact_repair_from_raw_s40_seed10101/candidate_checkpoint.pt
```

Exact objective retention versus M349:

| Objective | Endpoint delta |
| --- | ---: |
| Exact M297 rejected-history preference | -0.000380516 |
| Exact M270 source-balanced outcome | -0.000209033 |

Both exact objectives pass no-regression at the repaired endpoint.

## Endpoint Proof Gates

The repaired endpoint is not acceptable despite the strong exact improvement.

Source-diverse protected gate:

```text
runs/m351_repaired_source_diverse_protected_gate
```

Result:

```text
3 / 5 replay gates pass
failure_types = [proof_washout]
```

Old-key neighborhood targeted replay:

```text
runs/m351_repaired_old_key_neighborhood_targeted_replay
```

Result:

```text
25 / 40 compact rows accepted
37 / 40 normal-success rows retained
policy_pass = false
```

The endpoint is therefore a useful PPO/repair direction, but too large for the
proof surfaces.

## Bounded Interpolation

M351 runs the registered interpolation from the M349 base to the repaired
endpoint:

```text
runs/m351_m349_to_repaired_old_key_neighborhood_interpolation
```

Old-key neighborhood targeted replay and gate results:

| Policy | Alpha | Accepted rows | Old-key gate | Repair needed | Gap p10 | Gap min |
| --- | ---: | ---: | --- | --- | ---: | ---: |
| m351_a000 | 0.0000 | 40 / 40 | true | false | 0.000000 | 0.000000 |
| m351_a0025 | 0.0025 | 40 / 40 | true | false | -0.000006 | -0.000016 |
| m351_a005 | 0.0050 | 40 / 40 | true | false | -0.000012 | -0.000032 |
| m351_a0075 | 0.0075 | 40 / 40 | true | false | -0.000018 | -0.000048 |
| m351_a010 | 0.0100 | 39 / 40 | false | false | -0.000023 | -0.000064 |
| m351_a1000 | 1.0000 | 25 / 40 | false | true | -0.004023 | -0.050462 |

The largest passing alpha in the registered grid is:

```text
alpha = 0.0075
```

The first failing alpha is:

```text
alpha = 0.01
```

## Selected Candidate Gates

Selected candidate:

```text
runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt
```

Exact objective retention versus M349:

| Objective | Selected delta | Pass |
| --- | ---: | --- |
| Exact M297 rejected-history preference | -0.000002742 | true |
| Exact M270 source-balanced outcome | -0.000001490 | true |

Source-diverse protected gate:

```text
runs/m351_a0075_source_diverse_protected_gate
```

All five source-diverse protected replay gates pass.

| Replay gate | Rows | Candidate drops | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| current_m333_surface | 17 | 17 | +0.000010121 | +0.000005954 | true |
| m328_continuity_surface | 17 | 17 | +0.000100758 | +0.000043684 | true |
| m325_continuity_surface | 17 | 17 | +0.000294593 | +0.000128562 | true |
| m317_continuity_surface | 17 | 17 | +0.000489393 | +0.000208808 | true |
| m314_continuity_surface | 17 | 17 | +0.000489915 | +0.000209009 | true |

First replay gates:

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M170 | 17 | 17 / 17 | +0.000011870 | +0.000002073 | true |
| M267/M264 | 17 | 17 / 17 | +0.000010120 | +0.000005951 | true |

## Interpretation

M351 is a mixed positive result.

Positive:

```text
raw PPO completes,
exact repair finds a strong exact-objective improvement,
bounded alpha 0.0075 passes exact/source-diverse/old-key-neighborhood/first replay gates.
```

Limitation:

```text
the repaired endpoint washes out source-diverse and old-key neighborhood proof,
and the accepted movement is again limited to alpha 0.0075.
```

This supports a full public gate for the bounded candidate. It also shows that
the old-key neighborhood gate behaves as intended: it allows a small safe step
but rejects the endpoint and catches the first unsafe alpha at `0.01`.

## Decision

Admit:

```text
m352-full-public-gate-for-m351-a0075
```

Decision:

```text
admit_m352_full_public_gate_for_m351_a0075
```
