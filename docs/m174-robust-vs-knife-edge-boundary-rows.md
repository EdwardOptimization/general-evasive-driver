# M174 Robust Versus Knife-Edge Boundary Rows

M173 showed that the M170/M171 failures are tiny margin flips on fragile rows.
M174 classifies the M168 boundary replay rows by margin slack to separate robust
promotion rows from knife-edge stress diagnostics.

This is a positive gate-design result. The rows that M170/M171 lose are exactly
the smallest-slack rows under the admitted M168 checkpoint.

## Slack Definition

For a success-drop row:

```text
normal_success = true
wrong_history_success = false
min_slack = min(normal_margin, -wrong_history_margin)
```

Large `min_slack` means both the normal rollout and wrong-history rollout have
margin room. Small `min_slack` means the row is close to a binary outcome flip.

## M168 Success-Drop Rows

M168 has `16` success-drop rows in the fixed M164 replay corpus.

| Threshold | Robust rows | Knife-edge rows |
| ---: | ---: | ---: |
| 0.00025 | 13 | 3 |
| 0.00050 | 13 | 3 |
| 0.00100 | 11 | 5 |
| 0.00200 | 5 | 11 |
| 0.00500 | 0 | 16 |

Rows sorted by `min_slack`:

| Row | Target | Physical pair | Normal margin | Wrong margin | Min slack |
| ---: | --- | --- | ---: | ---: | ---: |
| 67 | future_lateral_accel_response | 9530:21:9540:24 | 0.006979 | -0.000179 | 0.000179 |
| 70 | future_lateral_accel_response | 9518:15:9550:21 | 0.000186 | -0.005647 | 0.000186 |
| 77 | future_lateral_accel_response | 9518:15:9550:18 | 0.000186 | -0.004986 | 0.000186 |
| 56 | future_lateral_accel_response | 9530:18:9540:21 | 0.006887 | -0.000828 | 0.000828 |
| 17 | future_yaw_response | 9519:3:9526:3 | 0.000865 | -0.000968 | 0.000865 |
| 54 | future_braking_deceleration | 9530:24:9540:30 | 0.007050 | -0.001053 | 0.001053 |
| 9 | future_braking_deceleration | 9530:15:9550:18 | 0.001409 | -0.007384 | 0.001409 |
| 11 | future_lateral_accel_response | 9530:18:9540:21 | 0.001894 | -0.005814 | 0.001894 |
| 6 | future_lateral_accel_response | 9530:18:9540:24 | 0.001894 | -0.008715 | 0.001894 |
| 12 | future_lateral_accel_response | 9530:21:9540:24 | 0.001985 | -0.005166 | 0.001985 |
| 7 | future_braking_deceleration | 9530:21:9540:27 | 0.001985 | -0.007445 | 0.001985 |
| 10 | future_braking_deceleration | 9530:24:9540:30 | 0.002055 | -0.006038 | 0.002055 |
| 48 | future_braking_deceleration | 9530:15:9550:18 | 0.006402 | -0.002405 | 0.002405 |
| 41 | future_braking_deceleration | 9530:21:9540:27 | 0.006979 | -0.002461 | 0.002461 |
| 15 | future_yaw_response | 9542:3:9549:3 | 0.002618 | -0.002824 | 0.002618 |
| 33 | future_lateral_accel_response | 9530:18:9540:24 | 0.006887 | -0.003733 | 0.003733 |

## Failure Rows

M170 lost row:

| Row | M168 min slack | Class at 0.0005 | Class at 0.001 |
| ---: | ---: | --- | --- |
| 67 | 0.000179 | knife-edge | knife-edge |

M171 lost rows:

| Row | M168 min slack | Class at 0.0005 | Class at 0.001 |
| ---: | ---: | --- | --- |
| 70 | 0.000186 | knife-edge | knife-edge |
| 77 | 0.000186 | knife-edge | knife-edge |

At threshold `0.0005`, the observed lost rows are exactly the knife-edge rows.
At threshold `0.001`, rows `56` and `17` become a low-margin watchlist, but they
were not lost by M170 or M171.

## Decision

Future gates should separate:

- robust promotion rows: success-drop rows with `min_slack >= 0.001`;
- low-margin watchlist rows: `0.0005 <= min_slack < 0.001`;
- knife-edge stress rows: `min_slack < 0.0005`.

This split does not discard knife-edge rows. It changes their role:

- robust rows should be hard promotion criteria;
- knife-edge rows should be reported as stress diagnostics;
- losing knife-edge rows should trigger analysis, but should not be the only
  reason to reject a candidate if robust rows and behavior gates pass.

The next step should implement or document a margin-split replay guard and
evaluate M168, M170, and M171 under that split before deciding whether any
stage2 checkpoint deserves behavior/protected-key evaluation.

## Validation

Evidence inspected:

```text
runs/m168_from_m167_5168_boundary_outcome_replay_gate_seed9510/boundary_replay_rows.csv
runs/m170_boundary_outcome_replay_gate_seed9510/boundary_replay_rows.csv
runs/m171_boundary_outcome_replay_gate_seed9510/boundary_replay_rows.csv
```
