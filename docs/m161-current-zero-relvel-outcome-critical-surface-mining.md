# M161 Current Zero-Relvel Outcome-Critical Surface Mining

Date: 2026-05-22

## Question

M160 showed that the M159 current zero-relvel matched-history surface is
action-sensitive but outcome-neutral:

```text
wrong history changes the first action,
but it does not reliably change continuation success or clearance margin.
```

M161 asks whether the same current zero-relvel surface can be relocated toward
the obstacle boundary so that wrong matched history becomes outcome-critical.

This is not PPO and not driver promotion. It is a gate-time proof-surface
construction using the same actor input contract.

## M156 Boundary Relocation

Run:

```text
runs/m161_m156_boundary_relocation_zero_relvel_seed9510
```

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy m156_s20=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --outcome-csv runs/m160_m156_outcome_gate_zero_relvel_allpairs_seed9510/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 40 \
  --max-pairs-per-checkpoint-target 20 \
  --min-base-action-distance 0.02 \
  --target-normal-margins 0.005,0.01,0.02,0.05,0.10,0.15 \
  --half-width-inflations 0 \
  --min-margin-gap 0.005 \
  --min-accepted-wrong-rows 6 \
  --report-variants wrong_matched_history,reset_hidden,zero_current_response,zero_action_history,delayed_history \
  --device cpu \
  --run-dir runs/m161_m156_boundary_relocation_zero_relvel_seed9510
```

Aggregate result:

| Metric | Value |
| --- | ---: |
| candidate rows | 60 |
| replay rows | 2100 |
| accepted wrong-history rows | 238 |
| accepted wrong-history source pairs | 45 |
| wrong-history success drops | 51 |
| accepted reset rows | 150 |
| accepted zero-current rows | 150 |
| surface found | true |

Wrong-history by target:

| Target | Accepted rows | Success drops | Mean gap | Max gap |
| --- | ---: | ---: | ---: | ---: |
| braking | 104 | 26 | 0.011870 | 0.025283 |
| lateral | 106 | 17 | 0.006750 | 0.010295 |
| yaw | 28 | 8 | 0.001961 | 0.006279 |

## M142 Calibration

Run:

```text
runs/m161_m142_boundary_relocation_zero_relvel_seed9510
```

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy m142_a400=runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --outcome-csv runs/m160_m142_outcome_calibration_zero_relvel_allpairs_seed9510/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 40 \
  --max-pairs-per-checkpoint-target 20 \
  --min-base-action-distance 0.02 \
  --target-normal-margins 0.005,0.01,0.02,0.05,0.10,0.15 \
  --half-width-inflations 0 \
  --min-margin-gap 0.005 \
  --min-accepted-wrong-rows 6 \
  --report-variants wrong_matched_history,reset_hidden,zero_current_response,zero_action_history,delayed_history \
  --device cpu \
  --run-dir runs/m161_m142_boundary_relocation_zero_relvel_seed9510
```

Aggregate result:

| Metric | Value |
| --- | ---: |
| candidate rows | 60 |
| replay rows | 2040 |
| accepted wrong-history rows | 260 |
| accepted wrong-history source pairs | 47 |
| wrong-history success drops | 57 |
| accepted reset rows | 102 |
| accepted zero-current rows | 102 |
| surface found | true |

Wrong-history by target:

| Target | Accepted rows | Success drops | Mean gap | Max gap |
| --- | ---: | ---: | ---: | ---: |
| braking | 104 | 28 | 0.013978 | 0.028731 |
| lateral | 130 | 19 | 0.007945 | 0.012475 |
| yaw | 26 | 10 | 0.004161 | 0.013193 |

M142 calibration confirms that the surface is not a M156-only anomaly. The
current baseline family has an outcome-critical wrong-history boundary when the
obstacle is tightened to near-boundary margins.

## Robustness Check

M161 then checks whether accepted rows are dominated by a few duplicated source
pairs. The M116-style strict `20 physical pairs / 10 left steps` threshold was
too high for M156 (`16` physical pairs, `8` left steps), but the M154/M161
minimum target is much lower: at least `6` physical pairs, at least `5` decision
steps, all three targets, and no single source pair dominating.

M156 robustness:

```text
runs/m161_m156_boundary_robustness_m154_zero_relvel_seed9510
```

| Metric | Value |
| --- | ---: |
| accepted wrong rows | 238 |
| robustness physical pairs | 16 |
| left steps | 8 |
| right steps | 10 |
| targets | 3 |
| normal-margin buckets | 14 |
| success-drop fraction | 0.214286 |
| max rows / pair fraction | 0.117647 |
| pass | true |

M142 robustness:

```text
runs/m161_m142_boundary_robustness_m154_zero_relvel_seed9510
```

| Metric | Value |
| --- | ---: |
| accepted wrong rows | 260 |
| robustness physical pairs | 16 |
| left steps | 7 |
| right steps | 9 |
| targets | 3 |
| normal-margin buckets | 14 |
| success-drop fraction | 0.219231 |
| max rows / pair fraction | 0.107692 |
| pass | true |

The `accepted_wrong_history_pairs` value in the relocation summary counts source
pairs at the relocation harness level; the robustness harness uses stricter
deduplication over `(left_seed, left_step, right_seed, right_step)`. Both are
reported to avoid overstating independence.

## Interpretation

M161 is a positive proof-surface milestone:

- the current zero-relvel surface can be made outcome-critical by boundary
  relocation;
- wrong matched history produces actual success drops and margin losses;
- the signal appears for both M156 and M142;
- accepted rows cover braking, lateral, and yaw targets;
- robustness checks pass the M154/M161 minimum diversity gates.

This is still not a broad driver proof. It shows that the current surface has a
near-boundary outcome-critical version. It does not prove that the policy
already uses history robustly in unrelocated everyday cases, and it does not
admit PPO by itself.

## Decision

Complete M161 as a positive current zero-relvel outcome-critical surface mining
milestone.

Next task: convert this surface into a reusable current zero-relvel
boundary-outcome corpus/objective and gate it before PPO. Do not jump straight
to PPO from M161.
