# M317 Full Public Gate For M316 Alpha 0.0025

M317 runs the full public promotion gate for the M316 protected-key-bounded
alpha `0.0025` candidate. Actor inputs are unchanged.

## Candidate

Previous public-gate base:

```text
runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt
```

Candidate:

```text
runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt
```

Exact objective retention versus M314:

| Objective | Delta |
| --- | ---: |
| Exact M297 rejected-history preference | -0.000000477 |
| Exact M270 source-balanced outcome | -0.000000298 |

## Replay Gates

All six replay gates pass versus M314.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.000000593 | +0.000000076 | true |
| M183/M170 | 17 | 17 / 17 | +0.000000580 | +0.000000072 | true |
| M193/M189 | 14 | 14 / 14 | +0.000000525 | +0.000000201 | true |
| M212/M204 | 17 | 17 / 17 | +0.000000521 | +0.000000194 | true |
| M223/M219 | 17 | 17 / 17 | +0.000000524 | +0.000000198 | true |
| M267/M264 | 17 | 17 / 17 | +0.000000523 | +0.000000198 | true |

Replay run root:

```text
runs/m317_full_public_gate_for_m316_a0_0025/full_gates
```

## Protected Key

Protected key `9944|perturbed|28|28` passes and remains discriminative.

| Policy | Pass | Accepted cases | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: | ---: |
| m263_a005 | true | 1 / 1 | 0.199909 | 0.099300 | 0.100609 |
| m314_base | true | 1 / 1 | 0.199976 | 0.100100 | 0.099876 |
| m316_a0_0025 | true | 1 / 1 | 0.199995 | 0.100123 | 0.099873 |
| m239_a750 | false | 0 / 1 | 0.200336 | 0.099817 | 0.100519 |

`guard_validated = true`.

The selected candidate is very close to the protected-key normal-margin upper
window. The remaining slack to `0.2` is about `4.8e-6`.

## Behavior Retention

Behavior is retained on both public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m314_base | 0.8625 | 0.1375 | 1.835825 |
| 9505 | m316_a0_0025 | 0.8625 | 0.1375 | 1.835825 |
| 9505 | m316_a0_0025_reset | 0.8500 | 0.1500 | 1.834497 |
| 9505 | m316_a0_0025_zero_all | 0.8000 | 0.2000 | 1.853304 |
| 9506 | m314_base | 0.8625 | 0.1375 | 1.853346 |
| 9506 | m316_a0_0025 | 0.8625 | 0.1375 | 1.853346 |
| 9506 | m316_a0_0025_reset | 0.8500 | 0.1500 | 1.850783 |
| 9506 | m316_a0_0025_zero_all | 0.8000 | 0.2000 | 1.871215 |

The candidate keeps public behavior success and termination rates equal to M314
while preserving the reset and zero-all ablation ordering.

## Interpretation

M317 promotes M316 alpha `0.0025` as the new public-gate base. This is a valid
but tiny PPO-derived movement:

```text
M314 base -> M316 raw PPO proposal -> exact repair -> protected-key-bounded alpha 0.0025
```

The promotion confirms the acceptance stack still works, but it also exposes a
new blocker: the old protected key is now effectively saturated. Continuing PPO
without auditing the protected-key surface will likely produce only negligible
accepted movement.

## Decision

Promote:

```text
runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt
```

Decision:

```text
promote_m316_a0_0025_public_gate_base
```

Next:

```text
m318-m317-protected-key-slack-audit
```
