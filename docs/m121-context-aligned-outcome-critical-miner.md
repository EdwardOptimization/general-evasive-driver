# M121 Context-Aligned Outcome-Critical Miner

M120 found relaxed wrong-history margin-gap rows, but those rows failed the
strict current-context contract. M121 audits the context mismatch and tests a
stricter observation profile that removes obstacle relative velocity from the
actor context.

## Implementation

Updated code and config:

```text
src/autodrift/matched_action_corpus.py
tests/test_matched_action_corpus.py
configs/m121_human_view_zero_obstacle_relvel.json
```

Changes:

- `visible_observation_distances(...)` now reports separate road context,
  obstacle context, obstacle geometry, and obstacle relative-velocity
  distances;
- focused tests cover the new context-distance breakdown;
- the M121 env profile keeps the M24 human-view frame shape but sets
  `obstacle_relative_velocity_mode` to `zero`.

The profile change is intentionally narrow. It does not add privileged inputs or
alter the response stream; it removes a current-motion proxy from the obstacle
context so strict context matching can test the history-response channel more
cleanly.

Focused validation:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest -q tests/test_matched_action_corpus.py
```

Result:

```text
5 passed
```

## Diagnostic Run

The first run repeated the M120 relaxed M105 setup with context group distance
logging:

```text
runs/m121_context_group_m105_relaxed_seed9720
```

Result:

| Metric | Value |
| --- | ---: |
| Candidates | 507 |
| Visible matches | 408 |
| Accepted outcome rows | 7 |
| Selected rows | 3 |
| Selected physical pairs | 3 |
| Selected seeds | 2 |
| Outcome snippets | 7 |
| Max selected margin gap | 0.023294 |

The accepted relaxed rows had zero obstacle geometry distance. Their context
mismatch came almost entirely from obstacle relative velocity:

| Seed | Nominal step | Perturbed step | Body x | Half width | Context dist | Road dist | Obstacle rel-vel dist | Gap |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9728 | 39 | 36 | 12 | 0.7 | 0.266893 | 0.026897 | 0.265534 | 0.023294 |
| 9728 | 39 | 36 | 12 | 0.8 | 0.266893 | 0.026897 | 0.265534 | 0.023142 |
| 9728 | 39 | 36 | 11 | 0.7 | 0.246678 | 0.026897 | 0.245207 | 0.020452 |

Interpretation: the M120 context blocker was not obstacle position or size. It
was the obstacle relative-velocity fields, which encode ego velocity and yaw
rate in the static-obstacle task and therefore act as a response proxy inside
the context stream.

## Zero-Relvel Strict Runs

All strict M121 runs use:

```text
--max-visible-distance 0.75
--max-response-distance 0.35
--max-context-distance 0.05
--min-margin-gap 0.005
--max-normal-margin 0.20
--max-continuation-steps 40
--probe-strategy steer_brake
--probe-steer-amplitude 0.25
--probe-brake-level 0.20
--probe-period-steps 20
--bank-obstacle-distance-range 5,12
--bank-stride-steps 3
--bank-max-snapshots 30
--bank-max-pairs-per-seed 3
--snapshot-relocation-distances 10,11,12
--snapshot-relocation-lateral-offsets=-1
--snapshot-relocation-half-widths 0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4
--max-selected-per-physical-pair 1
--max-selected-per-seed 2
--outcome-export-min-margin-gap 0.005
--export-only-accepted-outcomes
```

Run directories:

```text
runs/m121_zero_relvel_m105_strict_10ep_seed9720
runs/m121_zero_relvel_m102_strict_10ep_seed9720
runs/m121_zero_relvel_m62_strict_10ep_seed9720
runs/m121_zero_relvel_m105_strict_30ep_seed9720
```

Summary:

| Policy/profile | Episodes | Candidates | Visible matches | Accepted rows | Selected rows | Selected physical pairs | Selected seeds | Snippets | Max snippet gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M105 zero-relvel strict | 10 | 507 | 240 | 7 | 3 | 3 | 2 | 7 | 0.026296 |
| M102 zero-relvel strict | 10 | 507 | 240 | 5 | 2 | 2 | 2 | 5 | 0.024894 |
| M62 zero-relvel strict control | 10 | 507 | 216 | 0 | 0 | 0 | 0 | 0 | 0.000000 |
| M105 zero-relvel strict | 30 | 1496 | 768 | 9 | 4 | 4 | 3 | 9 | 0.027255 |

The 30-episode M105 run is the main M121 evidence. It restored strict accepted
rows, including `5` success-drop source pairs and `328` margin-gap accepted
pairs before the source-diverse selection cap. After the source-diverse cap, the
selected set still covers only `4` physical pairs and `3` seeds.

Selected 30-episode rows:

| Seed | Nominal step | Perturbed step | Body x | Half width | Response dist | Context dist | Gap | Perturbed normal margin | Perturbed wrong margin |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9741 | 27 | 27 | 12 | 0.9 | 0.151218 | 0.041485 | 0.026935 | 0.010214 | -0.016721 |
| 9728 | 39 | 36 | 12 | 0.8 | 0.169944 | 0.026702 | 0.026296 | 0.043447 | 0.017151 |
| 9724 | 48 | 42 | 12 | 1.0 | 0.228495 | 0.012615 | 0.006110 | 0.173363 | 0.167253 |
| 9728 | 36 | 36 | 12 | 0.8 | 0.182813 | 0.017705 | 0.005379 | 0.043447 | 0.038068 |

## Interpretation

M121 is a useful input-audit and miner-infrastructure result, but it is not an
admitted training surface.

What improved:

- the context mismatch was localized to obstacle relative velocity;
- zeroing obstacle relative velocity restored strict accepted rows for M105 and
  M102;
- M62 remains a clean control with zero accepted rows under the same zero-relvel
  strict profile;
- accepted-only export continues to prevent non-admissible rows from entering
  training snippets.

What still fails:

- selected diversity is below the pre-registered target of at least `6`
  physical pairs and at least `5` source decision steps;
- most admitted rows are perturbed-side margin-gap rows rather than broad
  success-drop surfaces;
- the accepted set remains too small for a reliable wrong-history objective.

Decision: do not train an objective from M121 snippets yet.

The next research step should treat zero obstacle relative velocity as the
cleaner strict self-identification context profile, then broaden the source of
accepted rows before objective training. The promising path is either a wider
zero-relvel miner or a trained/evaluated zero-relvel policy profile, but the
gate remains the same: wrong-history degradation must be strict, source-diverse,
and control-clean.
