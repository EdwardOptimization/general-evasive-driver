# M320 Protected-Surface Objective Replay Conversion

M320 converts the M319 M317-family protected surface into compact
replay-aligned objective corpora. No PPO, actor update, promotion, or actor-input
change was performed.

## Inputs

Accepted rows:

```text
runs/m319_m317_family_boundary_robustness_seed9520/accepted_wrong_history_rows.csv
```

Source checkpoints:

```text
m316_a0_0025  runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt
m314_base     runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt
m316_repaired runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
```

`m316_a0_0025` remains the public-gate base.

## Corpus And Objective Results

All runs use:

```text
max_rows_per_physical_pair = 2
optimization_seeds = 10080,10081,10082
steps = 180
hidden_dim = 96
```

| Source | Rows | Physical pairs | Targets | Objective pass | Min combined improvement | Min delta improvement | Pairwise acc after |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `m316_a0_0025` | 17 | 13 | 2 | true | 2.054649 | 2.847497 | 1.0000 |
| `m314_base` | 17 | 13 | 2 | true | 2.054631 | 2.847475 | 1.0000 |
| `m316_repaired` | 17 | 13 | 2 | true | 2.067757 | 2.859305 | 1.0000 |

Artifacts:

- `runs/m320_m316_boundary_outcome_corpus_seed10080`
- `runs/m320_m314_boundary_outcome_corpus_seed10080`
- `runs/m320_m316_repaired_boundary_outcome_corpus_seed10080`

All compact corpora are source-diverse and replay-sized: `17` rows across `13`
physical-pair keys, capped at two rows per key.

The current-base `m316_a0_0025` corpus details:

| Metric | Value |
| --- | ---: |
| Rows | 17 |
| Physical pairs | 13 |
| Targets | 2 |
| `future_braking_deceleration` rows | 16 |
| `future_yaw_response` rows | 1 |
| Mean margin gap | 0.009644 |
| Max margin gap | 0.013077 |

## Replay Sanity

Artifacts:

- `runs/m320_m316_boundary_replay_sanity_seed10080`
- `runs/m320_m314_boundary_replay_sanity_seed10080`
- `runs/m320_m316_repaired_boundary_replay_sanity_seed10080`

| Corpus | Baseline | Candidate | Rows | Baseline drops | Candidate drops | Normal success delta | Gate pass |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `m316_a0_0025` | `m316_a0_0025` | `m314_base` | 17 | 17 | 17 | 0.0 | true |
| `m314_base` | `m314_base` | `m316_a0_0025` | 17 | 17 | 17 | 0.0 | true |
| `m316_repaired` | `m316_repaired` | `m316_a0_0025` | 17 | 17 | 17 | 0.0 | true |

Every corpus row replays as normal-history success and wrong-history failure
under its source checkpoint. Adjacent-family replay also preserves every
success-drop row under the configured retention thresholds.

## Interpretation

M320 is positive.

What it proves:

- the M319 source-diverse protected surface can be converted into compact
  boundary-outcome corpora;
- objective sanity passes on the current base, previous base, and repaired PPO
  endpoint;
- replay sanity preserves normal success and wrong-history failure across the
  compact corpora.

What it does not prove:

- that an actor update is safe;
- that PPO can continue from M317;
- that old key `9944` can be deleted.

The next step should design a source-diverse protected gate/objective using the
M320 compact corpora. The old key should remain a diagnostic, but it should not
remain the only hard veto once a replacement multi-surface gate is defined and
validated.

## Decision

Admit:

```text
m321-source-diverse-protected-gate-design
```

Decision:

```text
admit_m321_source_diverse_protected_gate_design
```
