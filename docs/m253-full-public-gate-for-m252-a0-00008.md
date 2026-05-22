# M253 Full Public Gate For M252 A0 00008

M253 runs the full public-gate stack for the largest M252 alpha that passed the
M183/M170 boundary audit. No PPO was run and actor inputs are unchanged.

## Candidate

Current public-gate base:

```text
runs/m250_nano_custom_m239_to_protected_source_interpolation/checkpoints/alpha_0_00005.pt
```

Candidate:

```text
runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt
```

M252 already showed the candidate improves exact source losses versus M239:

```text
M232 delta = -0.000014246
M223 source delta = -0.000012021
protected-key source delta = -0.000002194
```

## Replay Gates

All replay gates pass versus M250.

| Corpus | Rows | Success drops retained | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | -0.0000033 | -0.0000001 | true |
| M183 M170 | 17 | 17 / 17 | -0.0000033 | -0.0000001 | true |
| M193 M189 | 14 | 14 / 14 | -0.0000029 | -0.0000002 | true |
| M212 M204 | 17 | 17 / 17 | -0.0000031 | -0.0000002 | true |
| M223 M219 | 17 | 17 / 17 | -0.0000031 | -0.0000002 | true |

## Protected Key

Protected key `9944|perturbed|28|28` passes, and the guard remains
discriminative because `m239_a750` still fails.

| Policy | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m224_10063 | true | 0.186385 | 0.086925 | 0.099460 |
| m250_n00005 | true | 0.195854 | 0.095058 | 0.100797 |
| m252_a0_00008 | true | 0.195820 | 0.095022 | 0.100799 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

Run directory:

```text
runs/m253_critical_key_seed9944_a0_00008
```

## Behavior Retention

Behavior is retained on both public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m250_n00005 | 0.8625 | 0.1375 | 1.835355 |
| 9505 | m252_a0_00008 | 0.8625 | 0.1375 | 1.835353 |
| 9505 | m252_a0_00008_reset | 0.8500 | 0.1500 | 1.834004 |
| 9505 | m252_a0_00008_zero_all | 0.8000 | 0.2000 | 1.853245 |
| 9506 | m250_n00005 | 0.8625 | 0.1375 | 1.852872 |
| 9506 | m252_a0_00008 | 0.8625 | 0.1375 | 1.852870 |
| 9506 | m252_a0_00008_reset | 0.8500 | 0.1500 | 1.850273 |
| 9506 | m252_a0_00008_zero_all | 0.8000 | 0.2000 | 1.871153 |

## Decision

Promote `m252_a0_00008` as the current public-gate base:

```text
runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt
```

This is still not paper-level evidence. It is a public-gate base update that
preserves the fixed proof/behavior stack while improving the exact source
objective slightly more than M250.

Next step:

```text
m254-exact-source-gated-ppo-smoke-from-m253
```
