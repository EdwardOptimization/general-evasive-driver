# M267 Protected-Surface Objective Replay Conversion

M267 converts the M266 current-family protected surface into replay-aligned
boundary-outcome corpora. No PPO, actor update, promotion, or actor-input change
was performed.

## Inputs

Accepted rows:

```text
runs/m266_m264_family_boundary_robustness_seed9520/accepted_wrong_history_rows.csv
```

Source checkpoints:

```text
m264_a001  runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
m263_a005  runs/m263_m261_to_projection_interpolation/checkpoints/alpha_0_005.pt
m261_a001  runs/m261_m260_to_raw_interpolation/checkpoints/alpha_0_001.pt
```

`m264_a001` remains the public-gate base.

## Corpus And Objective Results

All runs use:

```text
max_rows_per_physical_pair = 2
optimization_seeds = 10070,10071,10072
steps = 180
hidden_dim = 96
```

| Source | Rows | Physical pairs | Targets | Objective pass | Min combined improvement | Min delta improvement | Pairwise acc after |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `m264_a001` | 17 | 13 | 2 | true | 2.744662 | 3.700353 | 1.0000 |
| `m263_a005` | 17 | 13 | 2 | true | 2.744635 | 3.700311 | 1.0000 |
| `m261_a001` | 17 | 13 | 2 | true | 2.744373 | 3.700063 | 1.0000 |

Artifacts:

- `runs/m267_m264_boundary_outcome_corpus_seed10070`
- `runs/m267_m263_boundary_outcome_corpus_seed10070`
- `runs/m267_m261_boundary_outcome_corpus_seed10070`

The compact corpora are source-diverse and replay-sized: `17` rows across `13`
physical-pair keys, capped at two rows per key.

The current-base `m264_a001` corpus details:

| Metric | Value |
| --- | ---: |
| Rows | 17 |
| Physical pairs | 13 |
| Targets | 2 |
| `future_braking_deceleration` rows | 16 |
| `future_yaw_response` rows | 1 |
| Mean normal margin | 0.006068 |
| Max normal margin | 0.010193 |
| Mean margin gap | 0.009434 |

## Replay Sanity

Artifacts:

- `runs/m267_m264_boundary_replay_sanity_seed10070`
- `runs/m267_m263_boundary_replay_sanity_seed10070`
- `runs/m267_m261_boundary_replay_sanity_seed10070`

| Corpus | Baseline | Candidate | Rows | Baseline drops | Candidate drops | Normal success delta | Gate pass |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `m264_a001` | `m264_a001` | `m263_a005` | 17 | 17 | 17 | 0.0 | true |
| `m263_a005` | `m263_a005` | `m264_a001` | 17 | 17 | 17 | 0.0 | true |
| `m261_a001` | `m261_a001` | `m264_a001` | 17 | 17 | 17 | 0.0 | true |

Every corpus row replays as normal-history success and wrong-history failure
under its source checkpoint. Adjacent-family candidate replay also preserves
every success-drop row under the configured retention thresholds.

## Decision

M267 is positive.

What it proves:

- the M266 source-diverse protected surface can be converted into compact
  boundary-outcome corpora;
- objective-only probes learn the protected-surface preference on all three
  current-family checkpoints;
- replay sanity preserves normal success and wrong-history failure for the
  current-base M264 corpus and the adjacent-family corpora.

What it does not prove:

- that an actor update is safe;
- that PPO can continue from M264;
- that the old protected key should be deleted.

Decision:

```text
admit_guarded_actor_update_design
```

Next step:

```text
m268-m267-guarded-actor-update-from-m264
```

M268 may run exactly one small M216/M224-style guarded actor update from
`m264_a001` using the M267 M264 corpus. It must preserve old replay surfaces,
the new M267 replay surface, the old protected-key diagnostic, and behavior
seeds before any repeat or PPO.
