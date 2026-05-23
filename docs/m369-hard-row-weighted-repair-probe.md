# M369 Hard-Row Weighted Repair Probe

M369 probes the hard-row weighted old-key repair path implemented in M368. It
does not run PPO and does not promote a checkpoint.

## Inputs

Base:

```text
runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt
```

First failing tested old-key interpolation:

```text
runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_2.pt
```

Weighted old-key corpus:

```text
runs/m368_old_key_preference_corpus_hard_row/old_key_preference_corpus.npz
```

## Exact Repair

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt \
  --raw-checkpoint runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_2.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --old-key-preference-npz runs/m368_old_key_preference_corpus_hard_row/old_key_preference_corpus.npz \
  --device cpu \
  --start-mode repair_from_raw \
  --steps 40 \
  --learning-rate 1e-5 \
  --exact-old-key-tolerance 1e-6 \
  --seed 10108 \
  --run-dir runs/m369_hard_row_weighted_repair_from_alpha02_s40_seed10108
```

Result:

| Metric | Value |
| --- | ---: |
| selected step | 39 |
| exact M297 delta vs base | -0.000342488 |
| exact M270 delta vs base | -0.000165403 |
| weighted old-key surrogate delta vs base | -0.021396160 |
| exact lexicographic pass | true |

Direct repaired endpoint:

```text
runs/m369_hard_row_weighted_repair_from_alpha02_s40_seed10108/candidate_checkpoint.pt
```

## Direct Old-Key Replay

Run dir:

```text
runs/m369_hard_row_repair_old_key_targeted_replay
runs/m369_hard_row_repair_old_key_replay_gate
```

Result:

```text
accepted rows: 37 / 40
candidate accepted regressions: 3
candidate normal-success regressions: 3
gate: fail
```

The direct repair overcorrects the hard-row side: the M366 hard row gets a
negative wrong-history margin again, but its normal-history branch becomes
negative. So the exact weighted surrogate is useful, but the endpoint is too
large for closed-loop proof gates.

## Bounded Interpolation

M369 interpolates from the M365 base to the direct repaired endpoint:

```text
runs/m369_hard_row_repair_interpolation
```

Closed-loop old-key compact replay:

```text
runs/m369_hard_row_interpolation_old_key_targeted_replay
```

| Interpolation alpha | Accepted rows | Normal-success rows | Gate note |
| ---: | ---: | ---: | --- |
| 0.05 | 40 / 40 | 40 / 40 | pass candidates |
| 0.10 | 40 / 40 | 40 / 40 | pass candidates |
| 0.20 | 40 / 40 | 40 / 40 | pass candidates |
| 0.40 | 40 / 40 | 40 / 40 | selected |
| 0.60 | 40 / 40 | 40 / 40 | fails gate on gap p10 |
| 0.80 | 38 / 40 | 38 / 40 | fails |
| 1.00 | 37 / 40 | 37 / 40 | fails |

Formal old-key replay gate for `a400`:

```text
runs/m369_hard_row_interp_a400_old_key_replay_gate
```

Result:

```text
candidate accepted regressions: 0
candidate normal-success regressions: 0
candidate gap p10: -0.000379703
candidate gate: pass
```

The larger `a600` candidate has no accepted regressions, but fails the compact
old-key gate because `candidate_gap_p10 = -0.000573217`, below the `-0.0005`
floor.

Selected proof-gate candidate:

```text
runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt
```

## Source-Diverse Protected Gate

Run dir:

```text
runs/m369_hard_row_a400_source_diverse_protected_gate
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
runs/m369_hard_row_a400_m183_m170_first_replay
runs/m369_hard_row_a400_m267_m264_first_replay
```

## Interpretation

M369 is positive as a proof-gate probe:

- hard-row weighted exact repair produces a much stronger exact/surrogate
  direction than the unweighted M364 endpoint;
- direct endpoint is too aggressive and fails old-key replay;
- interpolation alpha `0.4` from M365 base to the repaired endpoint passes
  old-key, source-diverse, and first replay proof gates;
- alpha `0.6` is the first tested old-key gate failure without accepted
  regressions, due to compact gap p10 erosion.

This is not yet a promoted driver. It should move to a full public gate.

## Decision

Admit:

```text
m370-full-public-gate-for-m369-a400
```

Decision:

```text
admit_m370_full_public_gate_for_m369_a400
```
