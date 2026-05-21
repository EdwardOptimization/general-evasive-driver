# M110 Current-Response Anchored Hidden-Envelope Objective

M110 tests the next hypothesis after M109:

```text
response_hidden must beat both reset_hidden and current_response;
beating reset_hidden alone is not enough to prove self-identification.
```

M109 showed that current response often predicts future envelope targets better
than carried recurrent hidden. M110 therefore extends the objective-only hidden
envelope optimizer with an explicit current-response baseline head and contrast
loss.

## Implementation

Updated:

```text
src/autodrift/hidden_envelope_optimize.py
src/autodrift/hidden_envelope_reliability_audit.py
tests/test_hidden_envelope_optimize.py
tests/test_hidden_envelope_reliability_audit.py
```

New optimizer options:

```text
--current-response-loss-coef
--current-response-contrast-coef
--current-response-contrast-margin
```

The training loss becomes:

```text
hidden_prediction_loss
+ reset_hidden_contrast
+ current_response_prediction_loss
+ current_response_contrast
```

The current-response prediction loss trains a separate baseline head. The
current-response contrast uses that baseline loss detached, so the objective
cannot win by making the current-response baseline worse.

The reliability audit now also reports:

```text
current_lift_mean
current_lift_min
current_pass_fraction
```

where current lift is:

```text
response_hidden_test_r2 - current_response_test_r2
```

## First Objective Run

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_optimize \
  --checkpoint runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 30 \
  --seed 9730 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --train-fraction 0.70 \
  --ridge 0.1 \
  --steps 200 \
  --batch-size 256 \
  --learning-rate 0.0001 \
  --contrast-coef 0.5 \
  --contrast-margin 0.02 \
  --contrast-mode per_target \
  --current-response-loss-coef 1.0 \
  --current-response-contrast-coef 1.0 \
  --current-response-contrast-margin 0.02 \
  --target-loss-weights 1.0 1.0 1.0 \
  --grad-clip-norm 1.0 \
  --device cpu \
  --run-dir runs/m110_current_response_anchor_objective_seed9730
```

Internal after-objective probe:

| target | hidden-reset lift | hidden-current lift |
| --- | ---: | ---: |
| braking | -0.001359 | 0.175005 |
| lateral | -0.024881 | 0.222704 |
| yaw | 0.197146 | 0.243536 |

This run made hidden beat current response on the fixed objective batch, but
braking/lateral still failed against reset hidden.

Reliability gate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_reliability_audit \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint-policy m110_9730=runs/m110_current_response_anchor_objective_seed9730/optimized_checkpoint.pt \
  --probe-seeds 9510,9511,9512 \
  --split-seeds 9610,9611,9612,9613,9614 \
  --sample-limits 800 \
  --episodes 30 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --ridge 0.1 \
  --device cpu \
  --mean-lift-threshold 0.0 \
  --min-lift-threshold 0.0 \
  --pass-fraction-threshold 1.0 \
  --run-dir runs/m110_current_response_anchor_reliability_seed9510
```

External reliability result:

| target | hidden-reset mean | hidden-reset pass fraction | hidden-current mean | hidden-current pass fraction |
| --- | ---: | ---: | ---: | ---: |
| braking | -0.384863 | 0.1333 | -0.491639 | 0.0667 |
| lateral | -1.018245 | 0.0000 | -0.912061 | 0.0667 |
| yaw | -0.784435 | 0.0667 | -1.012188 | 0.0000 |

The first variant fails external reliability.

## Broad Objective Run

The second variant uses more samples and stronger current-response contrast.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_optimize \
  --checkpoint runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 90 \
  --seed 9700 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 2400 \
  --train-fraction 0.70 \
  --ridge 0.1 \
  --steps 300 \
  --batch-size 512 \
  --learning-rate 0.0001 \
  --contrast-coef 1.0 \
  --contrast-margin 0.02 \
  --contrast-mode per_target \
  --current-response-loss-coef 1.0 \
  --current-response-contrast-coef 2.0 \
  --current-response-contrast-margin 0.02 \
  --target-loss-weights 1.0 1.0 1.0 \
  --grad-clip-norm 1.0 \
  --device cpu \
  --run-dir runs/m110_current_response_anchor_broad_objective_seed9700
```

Internal after-objective probe:

| target | hidden-reset lift | hidden-current lift |
| --- | ---: | ---: |
| braking | 0.002985 | 0.123662 |
| lateral | 0.015369 | 0.356737 |
| yaw | 0.073372 | 0.164812 |

The broad variant passes the objective batch on all targets.

Reliability gate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_reliability_audit \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint-policy m110_broad9700=runs/m110_current_response_anchor_broad_objective_seed9700/optimized_checkpoint.pt \
  --probe-seeds 9510,9511,9512 \
  --split-seeds 9610,9611,9612,9613,9614 \
  --sample-limits 800 \
  --episodes 30 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --ridge 0.1 \
  --device cpu \
  --mean-lift-threshold 0.0 \
  --min-lift-threshold 0.0 \
  --pass-fraction-threshold 1.0 \
  --run-dir runs/m110_broad_current_response_anchor_reliability_seed9510
```

External reliability result:

| target | hidden-reset mean | hidden-reset pass fraction | hidden-current mean | hidden-current pass fraction |
| --- | ---: | ---: | ---: | ---: |
| braking | -0.435452 | 0.0667 | -0.518338 | 0.0667 |
| lateral | -0.539276 | 0.0000 | -0.653002 | 0.2000 |
| yaw | -0.533478 | 0.1333 | -0.730686 | 0.0667 |

The broad variant also fails external reliability, although it is less bad on
lateral/yaw than the first variant.

## Decision

M110 is negative for current-response anchored objective-only tuning.

What worked:

- the optimizer can explicitly train against a current-response baseline;
- the broad variant passes its own objective-batch probe against both reset and
  current response;
- the reliability harness now measures both reset and current-response lifts.

What failed:

- neither variant generalizes to the repeated split / multi-seed reliability
  gate;
- external hidden-current lift remains negative on all targets;
- stronger contrast and more samples do not produce a deployable
  self-identification belief.

Conclusion: continuing to tune same-style hidden-envelope objective-only losses
is low leverage. The next proof surface should be explicitly
history-necessary: matched current response and scene, different prior
command-response histories, different correct capability or action outcome.

M111 should construct or audit a matched-current-response ambiguity corpus
before training another objective.
