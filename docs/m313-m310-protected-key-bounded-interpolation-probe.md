# M313 M310 Protected-Key-Bounded Interpolation Probe

M313 probes whether a smaller trust-region move from M307 toward the rejected
M310 repaired candidate can keep exact-objective gains while staying inside the
protected-key window. No PPO was run and actor inputs are unchanged.

## Interpolation

Base:

```text
runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
```

Target:

```text
runs/m310_exact_repair_from_raw_s40_seed10095/candidate_checkpoint.pt
```

Sweep:

```text
runs/m313_m307_to_m310_protected_key_bounded_interpolation
```

## Exact Objectives

Every tested alpha from `0.0` to `0.2` keeps exact M297 and exact M270
non-regressing versus M307.

| Alpha | Exact M297 delta | Exact M270 delta | Exact pass |
| ---: | ---: | ---: | --- |
| 0.00 | +0.000000 | +0.000000 | true |
| 0.05 | -0.000006 | -0.000004 | true |
| 0.10 | -0.000012 | -0.000008 | true |
| 0.12 | -0.000015 | -0.000009 | true |
| 0.14 | -0.000017 | -0.000011 | true |
| 0.15 | -0.000018 | -0.000012 | true |
| 0.16 | -0.000020 | -0.000013 | true |
| 0.18 | -0.000022 | -0.000014 | true |
| 0.20 | -0.000025 | -0.000016 | true |

## Protected-Key Sweep

Protected key:

```text
9944|perturbed|28|28
```

Run dir:

```text
runs/m313_m310_protected_key_sweep
```

| Policy | Accepted | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m313_a000 | true | 0.198863 | 0.098839 | 0.100023 |
| m313_a050 | true | 0.199263 | 0.099293 | 0.099971 |
| m313_a100 | true | 0.199660 | 0.099742 | 0.099918 |
| m313_a120 | true | 0.199817 | 0.099920 | 0.099897 |
| m313_a140 | true | 0.199976 | 0.100100 | 0.099876 |
| m313_a150 | false | 0.200053 | 0.100188 | 0.099865 |
| m313_a160 | false | 0.200130 | 0.100275 | 0.099854 |
| m313_a180 | false | 0.200285 | 0.100452 | 0.099833 |
| m313_a200 | false | 0.200439 | 0.100627 | 0.099812 |

The largest protected-key-passing alpha is:

```text
alpha = 0.14
```

Selected candidate:

```text
runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt
```

## First Replay Gates

### M183/M170

| Metric | Value |
| --- | ---: |
| Success drops retained | 17 / 17 |
| Normal margin mean delta | +0.000029 |
| Margin gap mean delta | +0.000004 |
| Gate pass | true |

### M267/M264

| Metric | Value |
| --- | ---: |
| Success drops retained | 17 / 17 |
| Normal margin mean delta | +0.000025 |
| Margin gap mean delta | +0.000011 |
| Gate pass | true |

## Interpretation

M313 is positive as a proof-stage trust-region repair. It confirms the M310
direction is not unusable, but its full step violates the protected-key
normal-margin window. A bounded step at alpha `0.14` keeps:

- exact M297 and M270 non-regression;
- protected-key acceptance;
- M183/M170 and M267/M264 first replay retention.

This is still not a promotion. It admits a separate full public-gate milestone.

## Decision

Admit:

```text
m314-full-public-gate-for-m313-a140
```

Decision:

```text
admit_m314_full_public_gate_for_m313_a140
```
