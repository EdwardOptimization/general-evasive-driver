# M299 Full Public Gate For M298 A020

M299 runs the full public-gate stack for the M298 selected alpha. No PPO was
run and actor inputs are unchanged.

## Candidate

Current public-gate base:

```text
runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
```

Candidate:

```text
runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
```

M298 already showed that the candidate improves both exact objectives:

```text
M297 rejected-preference loss delta = -0.0021904706954956055
Exact M270 loss delta = -0.0013321638107299805
```

## Replay Gates

All replay gates pass versus M290.

| Surface | Rows | Success drops retained | Normal success | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | 1.000000 | -0.000442 | -0.000019 | true |
| M183/M170 | 17 | 17 / 17 | 1.000000 | -0.000440 | -0.000019 | true |
| M193/M189 | 14 | 14 / 14 | 1.000000 | -0.000389 | -0.000034 | true |
| M212/M204 | 17 | 17 / 17 | 1.000000 | -0.000406 | -0.000032 | true |
| M223/M219 | 17 | 17 / 17 | 1.000000 | -0.000406 | -0.000032 | true |
| M267/M264 | 17 | 17 / 17 | 1.000000 | -0.000406 | -0.000033 | true |

The margin deltas are negative but far inside the configured `0.005` normal
margin tolerance, and every wrong-history success-drop count is retained.

## Protected Key

The old protected-key diagnostic passes and remains discriminative:

```text
runs/m299_full_public_gate_for_m298_a020/full_gates/critical_key_seed9944
guard_validated = true
```

| Policy | Pass | Accepted cases |
| --- | --- | ---: |
| m263_a005 | true | 1 / 1 |
| m272_base | true | 1 / 1 |
| m290x64_a500 | true | 1 / 1 |
| m298pref_a020 | true | 1 / 1 |
| m239_a750 | false | 0 / 1 |

## Behavior Retention

Behavior is retained on both public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m290x64_a500 | 0.8625 | 0.1375 | 1.836100 |
| 9505 | m298pref_a020 | 0.8625 | 0.1375 | 1.835803 |
| 9505 | m298pref_a020_reset | 0.8500 | 0.1500 | 1.834567 |
| 9505 | m298pref_a020_zero_all | 0.8000 | 0.2000 | 1.853449 |
| 9506 | m290x64_a500 | 0.8625 | 0.1375 | 1.853644 |
| 9506 | m298pref_a020 | 0.8625 | 0.1375 | 1.853336 |
| 9506 | m298pref_a020_reset | 0.8500 | 0.1500 | 1.850854 |
| 9506 | m298pref_a020_zero_all | 0.8000 | 0.2000 | 1.871371 |

The promoted candidate keeps the same public behavior success and termination
rates as M290.

## Interpretation

M299 promotes `m298pref_a020` as the current public-gate base. This is the first
checkpoint after M290 that both improves exact M270 and the rejected-history
preference objective while preserving the full public proof stack.

This does not by itself solve PPO proof washout. The raw M298 objective update
already showed that stronger pressure can break closed-loop replay, and M291/M294
showed that smoke PPO can still wash out M267/M264 wrong-history rows. The next
step should design a PPO guard that explicitly uses the rejected-history
preference signal before running another PPO smoke.

## Decision

Promote:

```text
runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
```

Decision:

```text
promote_m298pref_a020_public_gate_base
```

Next step:

```text
m300-rejected-preference-ppo-guard-design
```
