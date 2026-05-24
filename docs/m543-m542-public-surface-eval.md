# M543 M542 Public Surface Eval

## Purpose

M543 evaluates the M542 seed-3540 4096-step route-pilot checkpoints on the same
public frozen-source natural surfaces used by M537.

This is a public diagnostic eval. It does not tune, repair, or promote a
checkpoint.

## Commands

Each split used `autodrift.frozen_source_surface_eval` with:

```text
source checkpoint = runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
baselines =
  l0_s3540 = runs/m542_matched_l0_variance_seed3540/checkpoint.pt
  l2_s3540 = runs/m542_matched_l2_variance_seed3540/checkpoint.pt
  l3_s3540 = runs/m542_matched_l3_variance_seed3540/checkpoint.pt
max_pairs = 0
max_continuation_steps = 80
```

Artifacts:

```text
runs/m543_public_eval_m497_short_reveal
runs/m543_public_eval_m497_warmup_capability
runs/m543_public_eval_m487_near_threshold
runs/m543_public_eval_m487_late_high_energy
runs/m543_m542_public_surface_eval_aggregate/summary.json
```

## Route Counts

| Surface | Input Pairs | Source Snapshots | Outcome Rows | Invalid Rows |
| --- | ---: | ---: | ---: | ---: |
| M497 short reveal | `116` | `294` | `1329` | `21` |
| M497 warmup capability | `178` | `508` | `2073` | `21` |
| M487 near threshold | `157` | `371` | `1647` | `79` |
| M487 late high energy | `155` | `374` | `1683` | `59` |

The invalid rows match the same source-tail availability pattern seen in M537.
All three baseline metadata validations pass.

## All-Row Metrics

| Level | Rows | Success Rate | Completion Rate | Collision Rate | Return Mean | Margin Mean | Margin Median |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| L0 current observation | `2244` | `0.800802` | `0.799020` | `0.199198` | `35.718019` | `1.384059` | `1.096702` |
| L2 finite window | `2244` | `0.866310` | `0.862745` | `0.133690` | `38.202276` | `1.777833` | `1.524142` |
| L3 online GRU | `2244` | `0.670677` | `0.668895` | `0.324421` | `28.966705` | `0.984809` | `0.619053` |

L2 is best on every aggregate metric. L3 is below both L0 and L2 on success,
completion, collision, return, and clearance margin.

## Per-Surface Result

| Surface | Level | Rows | Success Rate | Collision Rate | Return Mean | Margin Mean |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| M487 late high energy | L0 | `561` | `0.755793` | `0.244207` | `37.050371` | `1.025787` |
| M487 late high energy | L2 | `561` | `0.846702` | `0.153298` | `40.575990` | `1.425990` |
| M487 late high energy | L3 | `561` | `0.575758` | `0.418895` | `27.306842` | `0.649826` |
| M487 near threshold | L0 | `549` | `0.899818` | `0.100182` | `34.276359` | `1.897881` |
| M487 near threshold | L2 | `549` | `0.927140` | `0.072860` | `34.898408` | `2.111994` |
| M487 near threshold | L3 | `549` | `0.845173` | `0.154827` | `32.416624` | `1.588034` |
| M497 short reveal | L0 | `443` | `0.641084` | `0.358916` | `24.161966` | `0.614943` |
| M497 short reveal | L2 | `443` | `0.715576` | `0.284424` | `28.614083` | `0.889366` |
| M497 short reveal | L3 | `443` | `0.480813` | `0.516930` | `14.924117` | `0.450065` |
| M497 warmup capability | L0 | `691` | `0.861071` | `0.138929` | `43.190310` | `1.759776` |
| M497 warmup capability | L2 | `691` | `0.930535` | `0.069465` | `45.047051` | `2.367588` |
| M497 warmup capability | L3 | `691` | `0.730825` | `0.259045` | `36.576030` | `1.120332` |

L2 is best on every surface. L3 is worst on every surface.

## Paired Deltas

Positive success, completion, return, and margin deltas favor the first level in
the comparison. Negative collision deltas are better.

| Comparison | Rows | Success Delta | Completion Delta | Collision Delta | Return Delta | Margin Delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| L2 - L0 | `2244` | `+0.065508` | `+0.063725` | `-0.065508` | `+2.484257` | `+0.393774` |
| L3 - L0 | `2244` | `-0.130125` | `-0.130125` | `+0.125223` | `-6.751314` | `-0.399250` |
| L3 - L2 | `2244` | `-0.195633` | `-0.193850` | `+0.190731` | `-9.235571` | `-0.793024` |

Bootstrap 95% confidence intervals:

| Comparison | Metric | Mean | 95% CI Low | 95% CI High |
| --- | --- | ---: | ---: | ---: |
| L2 - L0 | success | `0.065508` | `0.055258` | `0.075769` |
| L2 - L0 | clearance margin | `0.393774` | `0.364816` | `0.423875` |
| L3 - L0 | success | `-0.130125` | `-0.143939` | `-0.116745` |
| L3 - L0 | clearance margin | `-0.399250` | `-0.426309` | `-0.372297` |
| L3 - L2 | success | `-0.195633` | `-0.211230` | `-0.179144` |
| L3 - L2 | clearance margin | `-0.793024` | `-0.841675` | `-0.742474` |

The public paired result is not ambiguous: seed-3540 L2 dominates, while seed
3540 L3 fails relative to both L0 and L2.

## M526 Event Overlay

M526 rows remain public diagnostics.

| Level | Event Rows | Event Success | Event Collision | Event Margin Mean |
| --- | ---: | ---: | ---: | ---: |
| L0 | `18` | `0.888889` | `0.111111` | `1.376383` |
| L2 | `18` | `1.000000` | `0.000000` | `4.172401` |
| L3 | `18` | `0.000000` | `0.888889` | `-0.011959` |

Event paired deltas show the same direction:

```text
L3 - L2 event success delta = -1.000000
L3 - L2 event margin delta  = -4.184361
```

## Interpretation

M543 confirms that the M542 route signal transfers to the public frozen-source
natural surfaces:

```text
For seed 3540 at 4096 steps, L2 is strong and L3 is a broad failure.
```

This does not disprove recurrent belief as a project direction. It does show
that the current L3 4096-step recipe is not ready for multi-seed expansion or
promotion. The next step should audit the recurrent recipe and training path
before spending more runs on the same L3 setup.

## Decision

```text
m542_public_eval_l2_dominant_l3_regression_admit_m544_l3_recipe_failure_audit
```
