# M130 Combined Outcome Formal Repeat Gate

M129 improved the fixed M128 corpus and retained behavior on two seeds. M130
tests whether that is enough to start PPO. It is not.

## Behavior Repeat

Run:

```text
runs/m130_combined_outcome_behavior_gate_seed9502
```

Environment:

```text
configs/m121_human_view_zero_obstacle_relvel.json
episodes=80
seed=9502
```

| Policy | Success | Termination | Return mean | Clearance mean | Clearance min |
| --- | ---: | ---: | ---: | ---: | ---: |
| M124 9821 | 0.8625 | 0.1375 | 65.673907 | 1.849902 | -0.125811 |
| M129 9830 | 0.8625 | 0.1375 | 65.871320 | 1.843562 | -0.186491 |
| M129 9830 reset | 0.8375 | 0.1625 | 63.386677 | 1.848242 | -0.169918 |
| M129 9830 zero-current | 0.8000 | 0.2000 | 60.856810 | 1.862968 | -0.147615 |
| M129 9830 zero-all | 0.8000 | 0.2000 | 60.856810 | 1.862968 | -0.147615 |
| M129 9830 no-action | 0.8625 | 0.1375 | 65.421316 | 1.849544 | -0.161616 |

Behavior retention passes. Zero-response degradation repeats. No-action history
is still neutral.

## Strict Outcome-Surface Repeat

All strict miners use:

```text
configs/m121_human_view_zero_obstacle_relvel.json
episodes=60
max_visible_distance=0.75
max_response_distance=0.35
max_context_distance=0.05
min_margin_gap=0.005
max_normal_margin=0.20
export_only_accepted_outcomes=true
```

| Run | Accepted rows | Success-drop pairs | Selected pairs | Selected seeds | Snippets | Max snippet gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M129 seed 9860 | 14 | 8 | 5 | 4 | 14 | 0.015155 |
| M129 seed 9880 | 9 | 7 | 3 | 3 | 9 | 0.015155 |
| M124 seed 9860 | 23 | 9 | 6 | 4 | 23 | 0.035959 |
| M62 seed 9860 | 0 | 4 | 0 | 0 | 0 | 0.000000 |
| M62 seed 9880 | 0 | 3 | 0 | 0 | 0 | 0.000000 |

M62 remains clean, but M129 does not meet the prior strict proof-surface
diversity standard. It is also weaker than same-seed M124 on selected pairs,
snippets, weight sum, and max snippet gap.

All exported M129 snippets are still perturbed-source:

```text
{'perturbed': 14}
{'perturbed': 9}
```

## Decision

Reject PPO readiness.

What passed:

- fresh behavior retention matches M124;
- zero-current and zero-all response ablations still reduce success to
  `0.8000`;
- reset hidden reduces success to `0.8375`;
- M62 controls export zero snippets on two fresh miner seeds.

What failed:

- M129 strict proof-surface diversity falls to `5` selected pairs/`4` seeds and
  then `3` selected pairs/`3` seeds;
- the fresh M129 surface is below the M122/M127 diversity standard;
- M129 is weaker than M124 on same-seed strict mining;
- no-action history remains neutral;
- source-side coverage remains perturbed-only.

M129 is a useful fixed-corpus objective result, but it is not a PPO-ready
driver candidate. The next step is M131: repair proof-surface retention before
continuation training.
