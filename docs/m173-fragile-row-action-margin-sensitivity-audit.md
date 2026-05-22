# M173 Fragile Row Action-Margin Sensitivity Audit

M172 paused stage2 PPO because fixed objective improvements did not align with
full boundary replay retention. M173 inspects fragile rows `67`, `70`, and `77`
to understand whether failures are large policy changes or low-margin binary
flips.

This is a diagnostic result. The observed failures are caused by very small
margin changes on knife-edge rows, not by large action deviations.

## Row67: M168 Versus M170

Row `67`:

```text
target=future_lateral_accel_response
physical_pair_key=9530:21:9540:24
```

| Metric | M168 accepted | M170 failed | Delta |
| --- | ---: | ---: | ---: |
| normal success | true | true | unchanged |
| wrong-history success | false | true | flipped |
| normal margin | 0.006979 | 0.007378 | +0.000399 |
| wrong-history margin | -0.000179 | 0.000191 | +0.000370 |
| normal first steer | 0.680029 | 0.680928 | +0.000899 |
| normal first throttle | -0.119611 | -0.119417 | +0.000194 |
| normal first brake | 0.026485 | 0.027478 | +0.000993 |
| wrong first steer | 0.678466 | 0.679639 | +0.001173 |
| wrong first throttle | -0.038583 | -0.039792 | -0.001209 |
| wrong first brake | 0.085277 | 0.085745 | +0.000468 |

The row flips because the wrong-history margin crosses from slightly negative
to slightly positive. The first-action changes are tiny.

## Rows70 And 77: M168 Versus M171

Rows `70` and `77` share the same normal snapshot:

```text
target=future_lateral_accel_response
physical_pair_key=9518:15:9550:21  # row 70
physical_pair_key=9518:15:9550:18  # row 77
```

| Row | Metric | M168 accepted | M171 failed | Delta |
| ---: | --- | ---: | ---: | ---: |
| 70 | normal success | true | false | flipped |
| 70 | wrong-history success | false | false | unchanged |
| 70 | normal margin | 0.000186 | -0.000298 | -0.000484 |
| 70 | wrong-history margin | -0.005647 | -0.006189 | -0.000542 |
| 77 | normal success | true | false | flipped |
| 77 | wrong-history success | false | false | unchanged |
| 77 | normal margin | 0.000186 | -0.000298 | -0.000484 |
| 77 | wrong-history margin | -0.004986 | -0.005516 | -0.000530 |

Normal first-action deltas for both rows:

| Action | M168 accepted | M171 failed | Delta |
| --- | ---: | ---: | ---: |
| steer | 0.640489 | 0.640347 | -0.000143 |
| throttle | -0.183483 | -0.182589 | +0.000894 |
| brake | -0.040626 | -0.041584 | -0.000958 |

Again, the action changes are tiny. The rows were already almost exactly on the
collision boundary under M168.

## Interpretation

The fragile rows are useful stress tests, but they are poor standalone PPO
promotion signals:

- row `67` fails when wrong-history margin moves by about `0.00037`;
- rows `70` and `77` fail when normal margin moves by about `0.00048`;
- first-action deltas are all around `0.001` or smaller;
- fixed objective can improve while these binary outcomes flip.

This means the current boundary replay corpus contains knife-edge cases where
small numerical or policy changes alter pass/fail status. A hard binary gate on
these rows is useful for detecting regressions, but it can also block useful
learning unless robust-margin rows are separated from knife-edge rows.

## Decision

Do not run more stage2 PPO yet.

The next step should split the boundary replay evidence into:

- robust rows: normal and wrong-history margins have enough slack to support
  stable promotion decisions;
- knife-edge rows: rows such as `67`, `70`, and `77` that should remain stress
  diagnostics but not be the only promotion criterion.

After that split, the project can decide whether to create a replay-aligned
margin objective or keep M168 as the accepted checkpoint while returning to
self-identification evidence.

## Validation

Evidence inspected:

```text
runs/m168_from_m167_5168_boundary_outcome_replay_gate_seed9510/boundary_replay_rows.csv
runs/m170_boundary_outcome_replay_gate_seed9510/boundary_replay_rows.csv
runs/m171_boundary_outcome_replay_gate_seed9510/boundary_replay_rows.csv
```
