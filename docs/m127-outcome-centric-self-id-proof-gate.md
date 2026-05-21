# M127 Outcome-Centric Self-ID Proof Gate

M126 rejected hidden-envelope R2 as the primary proof surface for the
zero-relvel line. M127 tests whether strict zero-relvel wrong-history outcome
degradation repeats across fresh miner seeds while M62 remains clean.

## Gate

Admit the proof surface only if:

- M124 strict zero-relvel outcome-critical rows repeat across fresh miner seeds;
- source diversity stays above the M122/M126 thresholds;
- M62 control remains unadmitted under the same miner settings;
- source-side coverage is reported explicitly;
- the result is treated as proof-surface admission, not driver success.

All runs use the M121 zero obstacle-relative-velocity profile:

```text
configs/m121_human_view_zero_obstacle_relvel.json
```

and the same strict thresholds used in M122/M126:

```text
--episodes 60
--max-visible-distance 0.75
--max-response-distance 0.35
--max-context-distance 0.05
--min-margin-gap 0.005
--max-normal-margin 0.20
--max-continuation-steps 40
--probe-strategy steer_brake
--top-k 200
--max-selected-per-physical-pair 1
--max-selected-per-seed 2
--export-only-accepted-outcomes
```

## M124 Repeat Results

| Run | Accepted rows | Success-drop pairs | Selected rows | Selected physical pairs | Selected seeds | Snippets | Max snippet gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M124 seed 9720 | 15 | 12 | 7 | 7 | 6 | 14 | 0.046191 |
| M124 seed 9820 | 25 | 14 | 10 | 10 | 8 | 24 | 0.035959 |
| M124 seed 9840 | 25 | 11 | 8 | 8 | 7 | 24 | 0.035959 |

Accepted source coverage:

| Run | Accepted rows | Accepted seeds | Physical pairs | Source steps |
| --- | ---: | ---: | ---: | --- |
| M124 seed 9720 | 15 | 6 | 7 | 24, 27, 28, 30, 36, 42, 45, 48 |
| M124 seed 9820 | 25 | 8 | 10 | 13, 16, 27, 30, 32, 33, 34, 35, 37, 44, 47 |
| M124 seed 9840 | 25 | 7 | 8 | 13, 16, 27, 30, 32, 33, 35, 38 |

Selected-row examples:

| Run | Seed | Nominal step | Perturbed step | Body x | Half width | Response dist | Context dist | Gap | Perturbed normal margin | Perturbed wrong margin | Success drop |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9820 | 9873 | 30 | 30 | 11 | 1.0 | 0.166617 | 0.021442 | 0.035959 | 0.155124 | 0.119165 | 0 |
| 9820 | 9872 | 30 | 30 | 10 | 0.7 | 0.167256 | 0.024667 | 0.011213 | 0.001785 | -0.009428 | 1 |
| 9840 | 9873 | 30 | 30 | 11 | 1.0 | 0.166617 | 0.021442 | 0.035959 | 0.155124 | 0.119165 | 0 |
| 9840 | 9880 | 38 | 35 | 12 | 1.2 | 0.182884 | 0.048764 | 0.010783 | 0.010204 | -0.000579 | 1 |

All exported snippets are perturbed-source rows:

| Run | Source counts |
| --- | --- |
| M124 seed 9720 | `{'perturbed': 14}` |
| M124 seed 9820 | `{'perturbed': 24}` |
| M124 seed 9840 | `{'perturbed': 24}` |

This is an explicit limitation: M127 admits a low-friction/perturbed-side
wrong-history proof surface, not a symmetric nominal/perturbed surface.

## M62 Controls

| Run | Accepted rows | Success-drop pairs | Selected rows | Selected physical pairs | Selected seeds | Snippets |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M62 seed 9720 | 0 | 0 | 0 | 0 | 0 | 0 |
| M62 seed 9820 | 0 | 2 | 0 | 0 | 0 | 0 |
| M62 seed 9840 | 0 | 3 | 0 | 0 | 0 | 0 |

The M62 controls can have raw success-drop counts before acceptance, but they do
not pass the strict visible/context/outcome/source-selection gate and export no
snippets.

## Decision

M127 admits the strict zero-relvel outcome-critical wrong-history surface as
the primary self-identification proof surface for the next stage.

What passed:

- M124 outcome-critical rows repeat across three miner seeds;
- each M124 run exceeds the M122/M126 diversity thresholds;
- M62 remains unadmitted across matching control seeds;
- strict context stays at `0.05`;
- exported snippets are accepted-only.

What remains limited:

- the surface is perturbed-source only;
- this is a proof-surface admission, not a full driver success claim;
- no-action history remains behavior-neutral from M125;
- PPO still requires a separate continuation gate.

Next step: M128 should build a combined M127 outcome snippet corpus and test an
outcome-centric objective/gate against that combined proof surface before any
PPO continuation.
