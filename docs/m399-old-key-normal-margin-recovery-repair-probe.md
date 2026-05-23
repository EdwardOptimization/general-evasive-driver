# M399 Old-Key Normal-Margin Recovery Repair Probe

M399 probes a no-PPO exact repair using the M398 old-key normal-margin recovery
targets plus the M393 current-family conflict corpus. It does not promote a
checkpoint and does not change the actor input/output contract.

## Inputs

Current public-gate base:

```text
runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
```

M398 old-key normal-margin recovery corpus:

```text
runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_corpus.npz
```

M393 current-family conflict corpus:

```text
runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz
```

## Repair Direction

The exact repair endpoint is:

```text
runs/m399_old_key_normal_margin_repair_s02_lexheavy_seed10135/candidate_checkpoint.pt
```

It improves exact losses but is too large for old-key closed-loop replay:

| Candidate | Exact pass | M267/M264 pass | Old-key accepted regressions | Main failure |
| --- | --- | --- | ---: | --- |
| s02 endpoint | true | true | 6 | old-key normal branch |

Endpoint exact deltas versus the M395 base:

| Metric | Delta |
| --- | ---: |
| exact M297 | -0.000567675 |
| exact M270 | -0.000330329 |
| old-key surrogate | -0.000926018 |

The endpoint still retains M267/M264 `17/17`, but cumulative old-key compact
replay falls to `34/40` accepted rows. This direction therefore needs a bounded
interpolation.

## Interpolation

Interpolation sweep:

```text
runs/m399_s02_interpolation
```

Old-key targeted replay:

```text
runs/m399_s02_interpolation_old_key_targeted_replay
```

| Alpha | Accepted rows | Policy pass |
| ---: | ---: | --- |
| 0.025 | 40 / 40 | true |
| 0.05 | 40 / 40 | true |
| 0.10 | 39 / 40 | false |
| 0.20 | 38 / 40 | false |
| 0.40 | 36 / 40 | false |
| 0.60 | 34 / 40 | false |
| 0.80 | 34 / 40 | false |
| 1.00 | 34 / 40 | false |

The formal old-key replay adapter passes alpha `0.05`:

```text
runs/m399_s02a050_old_key_replay_gate
```

and rejects alpha `0.10`:

```text
runs/m399_s02a100_old_key_replay_gate
```

Alpha `0.10` first fails the same old-key active case:

```text
9958|perturbed|39|36|9.500000|-1.200000|0.900000
```

At alpha `0.10`, the case has normal margin `-0.000085` and wrong-history
margin `-0.002228`, so this remains a normal-branch terminal-margin boundary,
not wrong-history sensitivity loss.

## Selected Candidate

Selected proof-gate candidate:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

Exact eval:

```text
runs/m399_s02a050_exact_eval
```

| Metric | Delta / value |
| --- | ---: |
| exact M297 delta | -0.000028372 |
| exact M270 delta | -0.000016451 |
| old-key surrogate delta | -0.000047207 |
| old-key recovery loss | 0.003873642 |
| current-family conflict loss | 0.001538875 |
| exact lexicographic pass | true |

## Proof Gates

M267/M264 first replay:

```text
runs/m399_s02a050_m267_m264_first_replay
```

| Metric | Value |
| --- | ---: |
| gate pass | true |
| success drops retained | 17 / 17 |
| wrong-history success rate | 0 |
| normal margin delta | -0.000060746 |
| margin gap delta | +0.000000977 |

M183/M170 first replay:

```text
runs/m399_s02a050_m183_m170_first_replay
```

| Metric | Value |
| --- | ---: |
| gate pass | true |
| success drops retained | 17 / 17 |
| wrong-history success rate | 0 |
| normal margin delta | -0.000064490 |
| margin gap delta | +0.000001031 |

Cumulative old-key compact replay:

```text
runs/m399_s02a050_old_key_replay_gate
```

| Metric | Value |
| --- | ---: |
| overall pass | true |
| accepted regressions | 0 |
| normal-success regressions | 0 |
| gap p10 | -0.000043084 |
| gap min | -0.000070740 |

Source-diverse protected gate:

```text
runs/m399_s02a050_source_diverse_protected_gate
```

| Metric | Value |
| --- | ---: |
| overall pass | true |
| replay gates passed | 5 / 5 |
| replay gates failed | 0 |

## Interpretation

The M398 normal-margin targets provide a useful direction, but old-key compact
replay again limits the trust region. Alpha `0.05` is the largest tested
old-key-passing point; alpha `0.10` first fails on the active `9958` normal
branch. This is a bounded proof-gate success, not a driver-level promotion.

## Decision

Admit a full public gate for the selected alpha `0.05` candidate:

```text
m400-full-public-gate-for-m399-s02a050
```
