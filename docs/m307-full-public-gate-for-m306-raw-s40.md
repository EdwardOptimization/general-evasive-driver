# M307 Full Public Gate For M306 Raw S40

M307 runs the full public-gate stack for the M306 raw-start exact repair
candidate. No PPO was run and actor inputs are unchanged.

## Candidate

Previous public-gate base:

```text
runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
```

Candidate:

```text
runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
```

Exact objective retention versus M299:

| Objective | M299 base | Candidate | Delta |
| --- | ---: | ---: | ---: |
| Exact M297 rejected-history preference | 1.189609528 | 1.189483285 | -0.000126243 |
| Exact M270 source-balanced outcome | 0.677945912 | 0.677865505 | -0.000080407 |

## Replay Gates

All six public replay gates pass versus M299.

| Surface | Rows | Success drops retained | Normal success | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | 1.000000 | +0.000214 | +0.000030 | true |
| M183/M170 | 17 | 17 / 17 | 1.000000 | +0.000211 | +0.000031 | true |
| M193/M189 | 14 | 14 / 14 | 1.000000 | +0.000191 | +0.000081 | true |
| M212/M204 | 17 | 17 / 17 | 1.000000 | +0.000188 | +0.000077 | true |
| M223/M219 | 17 | 17 / 17 | 1.000000 | +0.000188 | +0.000077 | true |
| M267/M264 | 17 | 17 / 17 | 1.000000 | +0.000188 | +0.000077 | true |

Replay run root:

```text
runs/m307_full_public_gate_for_m306_raw_s40/full_gates
```

## Protected Key

The old protected-key diagnostic passes and remains discriminative.

Run dir:

```text
runs/m307_full_public_gate_for_m306_raw_s40/full_gates/critical_key_seed9944
```

| Policy | Pass | Accepted cases |
| --- | --- | ---: |
| m263_a005 | true | 1 / 1 |
| m298pref_a020 | true | 1 / 1 |
| m306_raw_s40 | true | 1 / 1 |
| m239_a750 | false | 0 / 1 |

`guard_validated = true`.

## Behavior Retention

Behavior is retained on both public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m299_base | 0.8625 | 0.1375 | 1.835803 |
| 9505 | m306_raw_s40 | 0.8625 | 0.1375 | 1.835824 |
| 9505 | m306_raw_s40_reset | 0.8500 | 0.1500 | 1.834508 |
| 9505 | m306_raw_s40_zero_all | 0.8000 | 0.2000 | 1.853323 |
| 9506 | m299_base | 0.8625 | 0.1375 | 1.853336 |
| 9506 | m306_raw_s40 | 0.8625 | 0.1375 | 1.853346 |
| 9506 | m306_raw_s40_reset | 0.8500 | 0.1500 | 1.850793 |
| 9506 | m306_raw_s40_zero_all | 0.8000 | 0.2000 | 1.871236 |

The candidate keeps the same public behavior success and termination rates as
M299 while preserving the reset and zero-all ablation ordering.

## Interpretation

M307 promotes the M306 raw-start exact repair candidate as the new public-gate
base. This is the first checkpoint after M299 that:

- improves exact M297 and exact M270 versus M299;
- passes the full public replay stack;
- passes the protected-key diagnostic;
- retains behavior on seeds `9505` and `9506`.

The result is still one optimization seed. Before another PPO proposal or a
longer continuation, the repair recipe should be repeated with a fresh seed to
check seed fragility.

## Decision

Promote:

```text
runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
```

Decision:

```text
promote_m306_raw_s40_public_gate_base
```

Next:

```text
m308-exact-repair-fresh-seed-repeat
```
