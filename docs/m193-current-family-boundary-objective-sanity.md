# M193 Current-Family Boundary Objective Sanity

M192 produced a fresh current-family boundary wrong-history surface. M193 turns
that surface into replay-aligned boundary-outcome objective corpora before any
actor update or PPO.

This milestone does not train a policy. It only builds fixed corpora and checks
that a small risk regressor can learn the normal-history preference while replay
still reproduces normal success and wrong-history failure.

## Source Rows

Input:

```text
runs/m192_current_family_boundary_robustness_seed9520/accepted_wrong_history_rows.csv
```

The accepted M192 rows contain `131` wrong-history success drops across `11`
physical pairs, `6` left steps, `3` checkpoints, and `2` target groups.

## Corpus And Objective Results

All runs use:

```text
max_rows_per_physical_pair = 2
optimization_seeds = 9630,9631,9632
steps = 180
hidden_dim = 96
```

| Source checkpoint | Rows | Physical pairs | Targets | Objective pass | Min val combined improvement | Min val delta improvement | Min val pairwise acc |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| m184_s20 | 10 | 9 | 2 | true | 2.123931 | 2.713013 | 0.666667 |
| m188_5191 | 13 | 11 | 2 | true | 2.188185 | 3.035856 | 1.000000 |
| m189_5193 | 14 | 11 | 2 | true | 2.415990 | 3.080534 | 1.000000 |

Artifacts:

- `runs/m193_m184_boundary_outcome_corpus_seed9630`
- `runs/m193_m188_boundary_outcome_corpus_seed9630`
- `runs/m193_m189_boundary_outcome_corpus_seed9630`

The current-best M189 corpus is the primary one for the next actor-update
design.

M189 corpus details:

| Metric | Value |
| --- | ---: |
| Corpus rows | 14 |
| Physical pairs | 11 |
| Targets | 2 |
| Success-drop rows | 14 |
| Mean margin gap | 0.008583 |
| Max margin gap | 0.011878 |
| Max rows / physical pair | 2 |
| Max rows / physical pair fraction | 0.142857 |
| Action reconstruction error max | 0.0 |

## Replay Sanity

Artifacts:

- `runs/m193_m184_boundary_replay_sanity_seed9630`
- `runs/m193_m188_boundary_replay_sanity_seed9630`
- `runs/m193_m189_boundary_replay_sanity_seed9630`

| Corpus | Baseline | Candidate | Rows | Baseline drops | Candidate drops | Normal success delta | Gate pass |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| m184_s20 | m184_s20 | m189_5193 | 10 | 10 | 10 | 0.0 | true |
| m188_5191 | m188_5191 | m189_5193 | 13 | 13 | 13 | 0.0 | true |
| m189_5193 | m189_5193 | m188_5191 | 14 | 14 | 14 | 0.0 | true |

Every corpus row replays as normal-history success and wrong-history failure
under its source checkpoint. Cross-family candidate replay also preserves every
success-drop row under the configured retention thresholds.

## Decision

M193 is positive:

- all three current-family corpora pass 3-seed objective sanity;
- the M189 current-best corpus is replay-aligned and not duplicate-dominated;
- replay gates preserve every success-drop row across adjacent family
  checkpoints.

Decision:

```text
admit_current_best_guarded_actor_update_design
```

Next step:

```text
m194-current-best-guarded-actor-update
```

M194 may run only a tiny anchored actor update from M189. PPO remains blocked
until that actor update preserves behavior, protected key, old M183 replay
surfaces, and the refreshed M193 replay surface.
