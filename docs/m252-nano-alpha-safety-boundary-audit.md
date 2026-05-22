# M252 Nano Alpha Safety Boundary Audit

M252 maps the source-calibration alpha boundary discovered in M250 using the
fixed interpolation sweep from M251. No PPO was run and actor inputs are
unchanged.

## Setup

Base checkpoint:

```text
runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
```

Target checkpoint:

```text
runs/m249_protected_key_source_actor_coupling_probe/optimized_checkpoint.pt
```

Sweep:

```text
runs/m252_alpha_boundary_interpolation
```

The fixed interpolation tool generated collision-free checkpoints for:

```text
0.00005, 0.00006, 0.00007, 0.00008, 0.00009, 0.0001
```

## Exact Source Direction

Exact source-aware M232 loss improves monotonically as alpha increases.

| Policy | Alpha | Exact M232 | M223 source delta | Protected-key source delta |
| --- | ---: | ---: | ---: | ---: |
| m239_a500 | 0 | 0.244649455 | 0 | 0 |
| m252_a0_00005 | 0.00005 | 0.244640559 | -0.000007513 | -0.000001372 |
| m252_a0_00006 | 0.00006 | 0.244638771 | -0.000009021 | -0.000001648 |
| m252_a0_00007 | 0.00007 | 0.244637012 | -0.000010520 | -0.000001918 |
| m252_a0_00008 | 0.00008 | 0.244635209 | -0.000012021 | -0.000002194 |
| m252_a0_00009 | 0.00009 | 0.244633451 | -0.000013519 | -0.000002464 |
| m252_a0_0001 | 0.0001 | 0.244631678 | -0.000015032 | -0.000002737 |

Run directory:

```text
runs/m252_source_aware_exact_m232_eval
```

## M183/M170 Replay Boundary

The replay gate identifies a sharp proof-retention boundary.

| Policy | Alpha | Gate pass | Normal success | Success drops | Normal margin delta |
| --- | ---: | --- | ---: | ---: | ---: |
| m252_a0_00005 | 0.00005 | true | 1.000000 | 17 / 17 | -0.0000055 |
| m252_a0_00006 | 0.00006 | true | 1.000000 | 17 / 17 | -0.0000066 |
| m252_a0_00007 | 0.00007 | true | 1.000000 | 17 / 17 | -0.0000077 |
| m252_a0_00008 | 0.00008 | true | 1.000000 | 17 / 17 | -0.0000087 |
| m252_a0_00009 | 0.00009 | false | 0.941176 | 16 / 17 | -0.0000098 |
| m252_a0_0001 | 0.0001 | false | 0.941176 | 16 / 17 | -0.0000109 |

The cliff is row `16`:

```text
row_id = 16
target = future_braking_deceleration
physical_pair_key = 9530:6:9550:6
```

At `alpha=0.00008`, row 16 barely survives:

```text
normal_margin = 0.000000252
normal_success = true
```

At `alpha=0.00009`, it flips to collision:

```text
normal_margin = -0.000000645
normal_success = false
```

This proves the usable trust region is real and extremely narrow, not just an
artifact of the earlier rounded sweep.

## Decision

Do not promote `m252_a0_00008` yet. It passed only the boundary audit, not the
full public-gate stack.

Admit `m252_a0_00008` to full replay, protected-key, and behavior evaluation:

```text
runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt
```

Next step:

```text
m253-full-public-gate-for-m252-a0-00008
```
