# M449 Challenge Distribution Config Implementation

M449 implements the challenge distributions designed in M448 and runs
diagnostic smokes. It does not train, run PPO, promote a checkpoint, lower
proof gates, or change actor inputs/outputs.

## Configs

Added:

```text
configs/m449_challenge_near_threshold_zero_relvel.json
configs/m449_challenge_late_high_energy_zero_relvel.json
```

Both preserve the P0 human-view/no-wheel observation contract:

```text
history_length = 1
action_history_mode = full
obstacle_relative_velocity_mode = zero
wheel_observation_mode = none
```

The first strict late-high-energy draft failed scenario sampling. It was
relaxed before the committed benchmark by widening distance, narrowing obstacle
width slightly, and raising `max_threshold_score` to `0.30`. This keeps it a
hard challenge distribution but makes it usable.

## Near-Threshold Smoke

Benchmark:

```text
runs/m449_near_threshold_benchmark_seed9800
```

Miner:

```text
runs/m449_near_threshold_policy_difference_mining_seed9800
```

Policy summary:

| Policy | Success | Collision | Return | Mean margin | Min margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | `0.289062` | `0.703125` | `44.009521` | `0.071072` | `-0.305120` |
| M399 base | `0.882812` | `0.117188` | `75.715293` | `1.491319` | `-0.096490` |
| M427 high-utility rejected | `0.882812` | `0.117188` | `75.706330` | `1.491314` | `-0.098592` |
| M434 `r0010` proof-safe | `0.882812` | `0.117188` | `75.714265` | `1.491464` | `-0.097212` |
| M438 `r0015` proof-safe | `0.882812` | `0.117188` | `75.714516` | `1.491417` | `-0.097658` |
| M442 tail v2 rejected | `0.882812` | `0.117188` | `75.709833` | `1.491409` | `-0.097527` |

Policy-difference miner:

```text
comparison rows = 512
accepted rows   = 0
selected rows   = 0
```

Maximum absolute margin deltas versus M399:

| Policy | Max abs margin delta | Max abs return delta |
| --- | ---: | ---: |
| M427 high-utility rejected | `0.005282` | `0.109249` |
| M434 `r0010` proof-safe | `0.001942` | `0.041440` |
| M438 `r0015` proof-safe | `0.002780` | `0.049852` |
| M442 tail v2 rejected | `0.002459` | `0.072080` |

## Late High-Energy Smoke

Benchmark:

```text
runs/m449_late_high_energy_benchmark_seed9800
```

Miner:

```text
runs/m449_late_high_energy_policy_difference_mining_seed9800
```

Policy summary:

| Policy | Success | Collision | Return | Mean margin | Min margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | `0.210938` | `0.789062` | `38.994121` | `0.021009` | `-0.305321` |
| M399 base | `0.828125` | `0.171875` | `73.140016` | `1.222236` | `-0.103004` |
| M427 high-utility rejected | `0.828125` | `0.171875` | `73.142544` | `1.221992` | `-0.105094` |
| M434 `r0010` proof-safe | `0.828125` | `0.171875` | `73.145470` | `1.222249` | `-0.103806` |
| M438 `r0015` proof-safe | `0.828125` | `0.171875` | `73.139120` | `1.222175` | `-0.104102` |
| M442 tail v2 rejected | `0.828125` | `0.171875` | `73.141692` | `1.222173` | `-0.103999` |

Policy-difference miner:

```text
comparison rows = 512
accepted rows   = 0
selected rows   = 0
```

Maximum absolute margin deltas versus M399:

| Policy | Max abs margin delta | Max abs return delta |
| --- | ---: | ---: |
| M427 high-utility rejected | `0.003332` | `0.638392` |
| M434 `r0010` proof-safe | `0.001654` | `0.655047` |
| M438 `r0015` proof-safe | `0.001791` | `0.851108` |
| M442 tail v2 rejected | `0.001718` | `0.648106` |

## Interpretation

The challenge configs are valid and harder than M121, but they still do not
separate the recent candidate family.

The base success drops from the M447 M121 value `0.876953` to:

```text
near-threshold:   0.882812
late high-energy: 0.828125
```

The late high-energy config is meaningfully harder, but every candidate still
ties M399 on success and collision, and the miner finds zero outcome or margin
divergence rows in both configs.

This is now strong evidence that M427/M434/M438/M442 are effectively tiny local
perturbations of the same driver on these task distributions. Further repair of
this candidate family is not high leverage.

## Decision

M449 passes as an infrastructure/diagnostic milestone:

- both configs are committed;
- both 128-episode benchmark smokes run;
- both policy-difference miner smokes run;
- no checkpoint is promoted;
- no meaningful candidate-family divergence is found.

Admit:

```text
m450-challenge-response-ablation-benchmark
```

M450 should compare M399 normal behavior against response/history ablations on
the new challenge configs. If ablations degrade, the configs can still test
self-identification. If ablations do not degrade, the next branch should design
a richer task family rather than continuing with local checkpoint repair.
