# M364 Old-Key-Aware Repair Probe

M364 probes the M363 old-key-aware repair infrastructure. It does not run PPO
and does not promote a checkpoint.

## Candidate Family

Base:

```text
runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
```

Repair target:

```text
runs/m356_m354_repair_best_step_probe/candidate_checkpoint.pt
```

Old-key preference corpus:

```text
runs/m363_old_key_preference_corpus/old_key_preference_corpus.npz
```

## Exact Repair Probe

Default old-key tolerance:

```text
runs/m364_old_key_aware_repair_from_m356_s40_seed10105
```

Result:

```text
selected_alpha = 0.0
```

The default `1e-7` old-key surrogate tolerance was too tight for the tiny
floating-point delta on the old-key surrogate. Nonzero line-search alphas
regressed old-key surrogate by about `1.19e-7`, so the exact selector stayed at
the base.

Relaxed old-key tolerance:

```text
runs/m364_old_key_aware_repair_tol1e6_from_m356_s40_seed10106
```

Result:

| Metric | Value |
| --- | ---: |
| Repair selected alpha to M356 | 0.0025 |
| Exact M297 delta vs base | -0.000000358 |
| Exact M270 delta vs base | -0.000000238 |
| Old-key surrogate delta vs base | +0.000000119 |
| Exact lexicographic pass | true |

This candidate passed exact/surrogate metrics, but exact/surrogate metrics are
not proof.

## Closed-Loop Old-Key Replay

Direct repaired candidate:

```text
runs/m364_old_key_aware_repair_old_key_targeted_replay
runs/m364_old_key_aware_repair_old_key_replay_gate
```

Result:

```text
accepted rows: 39 / 40
accepted regressions: 1
gate: fail
```

The old-key surrogate improved candidate generation, but the direct repaired
candidate still failed closed-loop old-key proof.

M364 then interpolated from the M360 base to the repaired candidate:

```text
runs/m364_old_key_aware_repair_interpolation
```

Closed-loop old-key replay:

```text
runs/m364_old_key_aware_repair_interpolation_old_key_targeted_replay
```

| Interpolation alpha | Accepted rows | Gate |
| ---: | ---: | --- |
| 0.1 | 40 / 40 | pass |
| 0.2 | 39 / 40 | fail |
| 0.4 | 39 / 40 | fail |
| 0.6 | 39 / 40 | fail |
| 0.8 | 39 / 40 | fail |
| 1.0 | 39 / 40 | fail |

Selected proof-gate candidate:

```text
runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt
```

Old-key replay-gate artifact:

```text
runs/m364_old_key_aware_repair_alpha01_old_key_replay_gate
```

Result:

```text
accepted regressions: 0
gap p10: -0.000000980
gap min: -0.000001610
gate: pass
```

## Source-Diverse Protected Gate

Run dir:

```text
runs/m364_alpha01_source_diverse_protected_gate
```

Result:

```text
5 / 5 replay gates pass
```

## First Replay Gates

| Surface | Rows | Success drops retained | Gate |
| --- | ---: | ---: | --- |
| M183/M170 | 17 | 17 / 17 | pass |
| M267/M264 | 17 | 17 / 17 | pass |

Run dirs:

```text
runs/m364_alpha01_m183_m170_first_replay
runs/m364_alpha01_m267_m264_first_replay
```

## Interpretation

M364 is positive as a proof-gate probe, but still conservative:

- the old-key-aware repair direction can move beyond the M360 base under exact
  and surrogate objectives;
- the direct repaired candidate still fails closed-loop old-key replay by one
  accepted regression;
- interpolation alpha `0.1` from base to repaired candidate passes old-key,
  source-diverse, and first replay proof gates;
- alpha `0.2` is already the first failing tested old-key interpolation.

So this is not a large driver improvement. It is evidence that the M363
old-key-aware repair hook can produce a proof-gate-admissible incremental step.

## Decision

Admit a separate full public gate:

```text
m365-full-public-gate-for-m364-alpha01
```

Decision:

```text
admit_m365_full_public_gate_for_m364_alpha01
```
