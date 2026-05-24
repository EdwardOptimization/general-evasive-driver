# M544 L3 Variance Recipe Failure Audit

## Purpose

M544 audits why the M542/M543 L3 online-GRU variance recipe regresses while the
matched L2 finite-window recipe is strong.

This is a public diagnostic audit. It does not train, tune, or promote a
checkpoint.

## Artifacts

```text
runs/m544_l3_variance_recipe_failure_audit/summary.json
runs/m544_l3_variance_recipe_failure_audit/config_differences.csv
runs/m544_l3_variance_recipe_failure_audit/checkpoint_metadata.csv
runs/m544_l3_variance_recipe_failure_audit/train_metric_summary.csv
runs/m544_l3_variance_recipe_failure_audit/route_eval_summary.csv
runs/m544_l3_variance_recipe_failure_audit/public_aggregate_by_level.csv
runs/m544_l3_variance_recipe_failure_audit/public_paired_deltas.csv
runs/m544_l3_variance_recipe_failure_audit/m543_l3_l2_action_delta_summary.csv
runs/m544_l3_variance_recipe_failure_audit/m543_l3_l2_terminal_pairs.csv
```

## Config And Metadata

The L2/L3 config differences are exactly the intended history-level differences:

| Section | Key | L2 | L3 |
| --- | --- | --- | --- |
| ppo | actor encoder | `temporal_gru` | `human_view_online_gru` |
| ppo | actor history length | `4` | `1` |
| ppo | history baseline level | `L2_finite_window` | `L3_online_gru` |
| ppo | recurrent sequence training | missing / false | `true` |
| env | history length | `4` | `1` |

Checkpoint metadata is valid:

| Level | Input Contract | Uses Recurrent Hidden | Uses Finite Window | Total Steps | Seed |
| --- | --- | --- | --- | ---: | ---: |
| L2 | `P0_human_view_no_wheel_no_oracle` | `false` | `true` | `4096` | `3540` |
| L3 | `P0_human_view_no_wheel_no_oracle` | `true` | `false` | `4096` | `3540` |

There is no contract violation. The failure is in training behavior or recurrent
recipe quality, not in hidden/oracle input leakage.

## Training Dynamics

| Level | First 4 Return Mean | Last 4 Return Mean | Best Return | Best Step | Final Return | Last 4 Termination |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| L2 | `20.810138` | `44.089672` | `54.373740` | `3584` | `31.913302` | `0.612500` |
| L3 | `29.770559` | `23.259713` | `52.598733` | `1792` | `15.771149` | `0.937500` |

L3 is not incapable of learning a high-return behavior in this route. It peaks
early, then degrades. L2 improves later and remains much healthier near the end.

This points to recurrent recipe instability or missing checkpoint-selection
discipline, not to a final conclusion that online memory is useless.

## Route And Public Eval

Route eval from M542:

| Level | Return Mean | Termination Rate | Lateral RMSE | Beta Abs Error |
| --- | ---: | ---: | ---: | ---: |
| L0 | `20.334296` | `1.0` | `1.933182` | `0.211867` |
| L2 | `77.992665` | `0.2` | `0.664134` | `0.169140` |
| L3 | `21.645978` | `1.0` | `2.810300` | `0.166371` |

Public frozen-source eval from M543:

| Level | Success Rate | Collision Rate | Return Mean | Margin Mean |
| --- | ---: | ---: | ---: | ---: |
| L0 | `0.800802` | `0.199198` | `35.718019` | `1.384059` |
| L2 | `0.866310` | `0.133690` | `38.202276` | `1.777833` |
| L3 | `0.670677` | `0.324421` | `28.966705` | `0.984809` |

Paired public deltas:

| Comparison | Success Delta | Collision Delta | Return Delta | Margin Delta |
| --- | ---: | ---: | ---: | ---: |
| L2 - L0 | `+0.065508` | `-0.065508` | `+2.484257` | `+0.393774` |
| L3 - L0 | `-0.130125` | `+0.125223` | `-6.751314` | `-0.399250` |
| L3 - L2 | `-0.195633` | `+0.190731` | `-9.235571` | `-0.793024` |

L2 is currently the strong baseline. L3 is a broad regression in this recipe.

## Failure Pattern

M543 L3-L2 action and terminal summary:

| Subset | Rows | Success Delta | Collision Delta | Margin Delta | Steer Delta | Throttle Delta | Brake Delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | `2244` | `-0.195633` | `+0.190731` | `-0.793024` | `-0.534081` | `+0.374844` | `-0.254730` |
| success negative | `439` | `-1.000000` | `+0.974943` | `-1.707976` | `-0.576656` | `+0.378424` | `-0.273086` |
| margin negative | `1892` | `-0.231501` | `+0.226216` | `-0.943914` | `-0.541291` | `+0.376227` | `-0.259188` |

Terminal pairs:

| Terminal Pair | Rows | Success Delta | Margin Delta | Return Delta |
| --- | ---: | ---: | ---: | ---: |
| obstacle completed -> obstacle completed | `1501` | `0.000000` | `-0.669265` | `+2.545672` |
| obstacle completed -> collision | `423` | `-1.000000` | `-1.675839` | `-55.392903` |
| collision -> collision | `300` | `0.000000` | `-0.021293` | `-0.508052` |
| obstacle completed -> off road | `11` | `-1.000000` | `-2.579578` | `-53.485948` |

The dominant behavioral failure is:

```text
L2 completes obstacle -> L3 collides
```

This happens on `423` paired rows. L3 also loses margin on many rows where both
policies complete the obstacle.

## Interpretation

M544 rejects blind L3 multi-seed expansion for the current recipe.

The evidence supports this diagnosis:

- the P0 actor contract is intact;
- L3 has no hidden/oracle leakage issue;
- L3 can reach high rollout return early, so the architecture is not trivially
  unable to act;
- final L3 performance degrades after its early peak;
- public surface failures are broad and action-shifted;
- L2 finite-window history is a strong baseline and should remain in the main
  comparison.

The next milestone should design an L3 recurrent recipe repair before launching
more L3 training. Candidate controls:

- checkpoint interval and pre-registered model selection;
- lower recurrent update aggressiveness or smaller learning rate for a diagnostic
  L3-only repair branch;
- recurrent hidden-state rollout/truncation audit;
- compare online-GRU with finite-window GRU on identical sequence handling;
- add public-route health checks before public frozen-source eval.

Any repair branch is diagnostic until it is re-matched against L0/L2 with a
frozen recipe.

## Decision

```text
l3_recipe_failure_confirmed_admit_m545_recurrent_recipe_repair_design
```
