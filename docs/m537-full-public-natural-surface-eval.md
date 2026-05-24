# M537 Full Public Natural-Surface Eval

## Purpose

M537 runs the full public frozen-source natural-surface diagnostic matrix from
M536. It compares the nine matched short-train checkpoints:

```text
L0_current_observation: seeds 3530, 3531, 3532
L2_finite_window:       seeds 3530, 3531, 3532
L3_online_gru:          seeds 3530, 3531, 3532
```

All evaluations reconstruct frozen source states from the M399 public-gate base:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

This is a public diagnostic proof gate. It does not train, repair, or promote a
driver checkpoint.

## Commands

All four runs used `autodrift.frozen_source_surface_eval`, the same nine
baseline checkpoint matrix as M536, `--max-pairs 0`, CPU execution, and P0
metadata validation.

| Split | Env Config | Pairs CSV | Tail Offsets | Run Dir |
| --- | --- | --- | --- | --- |
| M497 short reveal | `configs/m494_natural_belief_short_reveal_zero_relvel.json` | `runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_short_reveal.csv` | `0,2,4,8` | `runs/m537_full_public_eval_m497_short_reveal` |
| M497 warmup capability | `configs/m494_natural_belief_warmup_capability_zero_relvel.json` | `runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_warmup_capability.csv` | `0,2,4,8` | `runs/m537_full_public_eval_m497_warmup_capability` |
| M487 near threshold | `configs/m484_critical_window_near_threshold_zero_relvel.json` | `runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_near_threshold.csv` | `4,8,12,16` | `runs/m537_full_public_eval_m487_near_threshold` |
| M487 late high energy | `configs/m484_critical_window_late_high_energy_zero_relvel.json` | `runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_late_high_energy.csv` | `4,8,12,16` | `runs/m537_full_public_eval_m487_late_high_energy` |

Aggregate artifacts:

```text
runs/m537_full_public_natural_surface_eval_aggregate/summary.json
runs/m537_full_public_natural_surface_eval_aggregate/run_counts.csv
runs/m537_full_public_natural_surface_eval_aggregate/surface_by_level.csv
runs/m537_full_public_natural_surface_eval_aggregate/aggregate_by_level.csv
runs/m537_full_public_natural_surface_eval_aggregate/aggregate_by_baseline.csv
runs/m537_full_public_natural_surface_eval_aggregate/event_overlay_by_level.csv
runs/m537_full_public_natural_surface_eval_aggregate/event_overlay_by_surface_level.csv
```

## Route Results

| Surface | Input Pairs | Source Snapshots | Outcome Rows | Invalid Rows |
| --- | ---: | ---: | ---: | ---: |
| M497 short reveal | `116` | `294` | `3987` | `21` |
| M497 warmup capability | `178` | `508` | `6219` | `21` |
| M487 near threshold | `157` | `371` | `4941` | `79` |
| M487 late high energy | `155` | `374` | `5049` | `59` |

The invalid rows are diagnosed source-tail availability misses, not checkpoint
metadata failures. All evaluated checkpoints kept
`P0_human_view_no_wheel_no_oracle` metadata, and no actor contract changed.

## All-Row Aggregate

Across all four public natural surfaces:

| Level | Rows | Success Rate | Obstacle Completion Rate | Collision Rate | Return Mean | Margin Mean | Margin Median |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| L0 current observation | `6732` | `0.831551` | `0.830214` | `0.168449` | `37.597130` | `1.510367` | `1.300026` |
| L2 finite window | `6732` | `0.833482` | `0.831699` | `0.166518` | `37.773384` | `1.540897` | `1.328011` |
| L3 online GRU | `6732` | `0.851901` | `0.850416` | `0.148099` | `38.439086` | `1.654668` | `1.485940` |

L3 has the best aggregate success, obstacle completion, collision, return, and
clearance margin. The advantage is strongest on margin and collision reduction:

```text
L3 - L0 success_rate = +0.020351
L3 - L2 success_rate = +0.018419
L3 - L0 margin_mean  = +0.144301
L3 - L2 margin_mean  = +0.113771
```

## Per-Surface Result

| Surface | Level | Rows | Success Rate | Completion Rate | Collision Rate | Return Mean | Margin Mean |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M487 late high energy | L0 | `1683` | `0.796197` | `0.796197` | `0.203803` | `39.805724` | `1.145861` |
| M487 late high energy | L2 | `1683` | `0.801545` | `0.799168` | `0.198455` | `40.078461` | `1.176002` |
| M487 late high energy | L3 | `1683` | `0.824718` | `0.824718` | `0.175282` | `40.947743` | `1.294032` |
| M487 near threshold | L0 | `1647` | `0.914390` | `0.914390` | `0.085610` | `35.189140` | `1.979649` |
| M487 near threshold | L2 | `1647` | `0.914997` | `0.914997` | `0.085003` | `35.333220` | `1.992239` |
| M487 near threshold | L3 | `1647` | `0.920461` | `0.920461` | `0.079539` | `35.291241` | `2.053074` |
| M497 short reveal | L0 | `1329` | `0.677201` | `0.677201` | `0.322799` | `26.459448` | `0.694478` |
| M497 short reveal | L2 | `1329` | `0.674191` | `0.674191` | `0.325809` | `26.481940` | `0.719641` |
| M497 short reveal | L3 | `1329` | `0.702784` | `0.702784` | `0.297216` | `28.150415` | `0.796392` |
| M497 warmup capability | L0 | `2073` | `0.893391` | `0.889050` | `0.106609` | `44.857561` | `1.956519` |
| M497 warmup capability | L2 | `2073` | `0.896768` | `0.892909` | `0.103232` | `45.079624` | `2.005059` |
| M497 warmup capability | L3 | `2073` | `0.915099` | `0.910275` | `0.084901` | `45.499421` | `2.181164` |

L3 is best on success and margin for every surface. L2 is usually slightly above
L0, but the gap is much smaller and not consistent on M497 short reveal success.

## M526 Event Overlay

M526 contributed `18` public diagnostic event keys. The M537 overlay matches
`162` outcome rows because each event key is evaluated by the nine checkpoint
matrix.

| Event Subset | Level | Rows | Success Rate | Completion Rate | Collision Rate | Return Mean | Margin Mean |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| non-event | L0 | `6678` | `0.830488` | `0.829140` | `0.169512` | `37.257245` | `1.505486` |
| non-event | L2 | `6678` | `0.832435` | `0.830638` | `0.167565` | `37.450237` | `1.534160` |
| non-event | L3 | `6678` | `0.850704` | `0.849206` | `0.149296` | `38.127963` | `1.642113` |
| M526 event | L0 | `54` | `0.962963` | `0.962963` | `0.037037` | `79.629471` | `2.114021` |
| M526 event | L2 | `54` | `0.962963` | `0.962963` | `0.037037` | `77.735879` | `2.374047` |
| M526 event | L3 | `54` | `1.000000` | `1.000000` | `0.000000` | `76.914645` | `3.207369` |

The event overlay supports the same direction as the all-row aggregate: L3 has
better obstacle completion and much larger clearance margin. Because these rows
are public diagnostics and only `18` event keys, this is not private-holdout or
paper-level evidence.

## Interpretation

M537 passes the public natural-surface diagnostic gate.

The evidence is stronger than M536 route smoke:

- full public matrix ran on all four natural splits;
- all nine checkpoint metadata validations passed;
- L3 is best on all-row aggregate metrics;
- L3 is best on every per-surface success and margin table;
- the M526 event overlay remains favorable to L3.

The correct claim is narrow:

```text
On public natural frozen-source diagnostic surfaces, the trained L3 online-GRU
baseline shows a repeatable advantage over matched L0/L2 short-train baselines.
```

The result does not prove final driver quality, private generalization, or
paper-level statistical significance. It also does not promote any checkpoint.
The next step should audit the advantage with paired keys, seed/surface
dominance checks, and confidence intervals before moving to fresh holdout
mining or additional training.

## Decision

```text
full_public_natural_eval_pass_admit_m538_paired_advantage_audit
```
