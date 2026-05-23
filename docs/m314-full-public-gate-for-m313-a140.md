# M314 Full Public Gate For M313 Alpha 0.14

M314 runs the full public promotion gate for the M313 protected-key-bounded
interpolation candidate. Actor inputs are unchanged.

## Candidate

Previous public-gate base:

```text
runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
```

Candidate:

```text
runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt
```

Exact objective retention versus M307:

| Objective | Delta |
| --- | ---: |
| Exact M297 rejected-history preference | -0.000017047 |
| Exact M270 source-balanced outcome | -0.000010908 |

## Replay Gates

All six replay gates pass versus M307.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.000029 | +0.000004 | true |
| M183/M170 | 17 | 17 / 17 | +0.000029 | +0.000004 | true |
| M193/M189 | 14 | 14 / 14 | +0.000026 | +0.000012 | true |
| M212/M204 | 17 | 17 / 17 | +0.000025 | +0.000011 | true |
| M223/M219 | 17 | 17 / 17 | +0.000025 | +0.000011 | true |
| M267/M264 | 17 | 17 / 17 | +0.000025 | +0.000011 | true |

Replay run root:

```text
runs/m314_full_public_gate_for_m313_a140/full_gates
```

## Protected Key

Protected key `9944|perturbed|28|28` passes and remains discriminative.

| Policy | Pass | Accepted cases | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: | ---: |
| m263_a005 | true | 1 / 1 | 0.199909 | 0.099300 | 0.100609 |
| m307_base | true | 1 / 1 | 0.198863 | 0.098839 | 0.100023 |
| m313_a140 | true | 1 / 1 | 0.199976 | 0.100100 | 0.099876 |
| m239_a750 | false | 0 / 1 | 0.200336 | 0.099817 | 0.100519 |

`guard_validated = true`.

## Behavior Retention

Behavior is retained on both public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m307_base | 0.8625 | 0.1375 | 1.835824 |
| 9505 | m313_a140 | 0.8625 | 0.1375 | 1.835825 |
| 9505 | m313_a140_reset | 0.8500 | 0.1500 | 1.834498 |
| 9505 | m313_a140_zero_all | 0.8000 | 0.2000 | 1.853304 |
| 9506 | m307_base | 0.8625 | 0.1375 | 1.853346 |
| 9506 | m313_a140 | 0.8625 | 0.1375 | 1.853346 |
| 9506 | m313_a140_reset | 0.8500 | 0.1500 | 1.850783 |
| 9506 | m313_a140_zero_all | 0.8000 | 0.2000 | 1.871216 |

The candidate keeps public behavior success and termination rates equal to M307
while preserving the reset and zero-all ablation ordering.

## Interpretation

M314 promotes M313 alpha `0.14` as the new public-gate base. This is a small
but valid PPO-derived movement:

```text
M307 base -> M310 raw PPO proposal -> exact repair -> protected-key-bounded alpha 0.14
```

The result confirms the current workflow:

```text
PPO proposal can be useful,
but exact repair and protected-key-bounded trust region are required before promotion.
```

## Decision

Promote:

```text
runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt
```

Decision:

```text
promote_m313_a140_public_gate_base
```

Next:

```text
m315-protected-key-aware-ppo-proposal-repeat-design
```
