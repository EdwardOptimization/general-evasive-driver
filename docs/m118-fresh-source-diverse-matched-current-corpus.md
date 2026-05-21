# M118 Fresh Source-Diverse Matched-Current Corpus

M117 showed that the M113/M115 boundary surface is exhausted: broader boundary
tuning still finds only the same `3` physical source pairs. M118 moves upstream
and mines a fresh matched-current-response ambiguity corpus with explicit source
diversity.

## Implementation

Updated `autodrift.matched_current_response_ambiguity` with:

```text
--max-pairs-per-physical-pair
```

The physical pair key is:

```text
(left_seed, left_step, right_seed, right_step)
```

The selector now greedily limits how often the same physical pair can be
selected within each checkpoint/probe-seed selection pass. This preserves the
visible/current-response ambiguity rule while reducing duplicate domination.

Focused validation:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  python -m pytest -q tests/test_matched_current_response_ambiguity.py

python -m compileall -q src tests
```

Result:

```text
4 passed
compileall passed
```

## Fresh Corpus Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy m62=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m102=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m105=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --probe-seeds 9510,9511 \
  --episodes 30 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --nearest-k 10 \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 200 \
  --max-pairs-per-physical-pair 1 \
  --min-accepted-pairs 30 \
  --device cpu \
  --run-dir runs/m118_source_diverse_matched_current_seed9510
```

Artifacts:

```text
runs/m118_source_diverse_matched_current_seed9510/summary.json
runs/m118_source_diverse_matched_current_seed9510/candidate_pairs.csv
runs/m118_source_diverse_matched_current_seed9510/matched_pairs.csv
runs/m118_source_diverse_matched_current_seed9510/target_summary.csv
```

## Fresh Corpus Result

| Metric | Value |
| --- | ---: |
| Candidate pairs | 89343 |
| Accepted pairs | 471 |
| Accepted physical pairs | 155 |
| Max rows per physical pair | 6 |
| Surface found | true |

Accepted pairs by checkpoint:

| Checkpoint | Rows | Physical pairs |
| --- | ---: | ---: |
| M62 | 160 | 114 |
| M102 | 155 | 106 |
| M105 | 156 | 105 |

Accepted pairs by target:

| Target | Rows | Physical pairs |
| --- | ---: | ---: |
| future braking deceleration | 303 | 107 |
| future lateral accel response | 97 | 31 |
| future yaw response | 71 | 18 |

Compared with the M115 accepted wrong-history surface, this is a much broader
upstream ambiguity corpus:

```text
M115 accepted wrong-history physical pairs: 3
M118 matched-current physical pairs: 155
```

## Action-Level Gate

M118 then repeats the M112 action-level history intervention gate on the fresh
corpus.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy m62=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m102=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m105=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --pairs-csv runs/m118_source_diverse_matched_current_seed9510/matched_pairs.csv \
  --delay-steps 10 \
  --min-action-distance 0.02 \
  --max-pairs-per-checkpoint-target 80 \
  --device cpu \
  --run-dir runs/m118_source_diverse_action_intervention_seed9510
```

Artifacts:

```text
runs/m118_source_diverse_action_intervention_seed9510/action_interventions.csv
runs/m118_source_diverse_action_intervention_seed9510/variant_summary.csv
runs/m118_source_diverse_action_intervention_seed9510/summary.json
```

Wrong-history aggregate:

| Metric | Value |
| --- | ---: |
| Rows | 408 |
| Physical pairs | 140 |
| Mean action distance | 0.066306 |
| Above-threshold fraction | 0.772059 |
| Closer-to-right fraction | 0.737745 |

By checkpoint:

| Checkpoint | Rows | Physical pairs | Mean action distance | Above threshold | Closer-to-right |
| --- | ---: | ---: | ---: | ---: | ---: |
| M62 | 136 | 101 | 0.062876 | 0.816176 | 0.647059 |
| M102 | 138 | 99 | 0.068538 | 0.717391 | 0.782609 |
| M105 | 134 | 95 | 0.067489 | 0.783582 | 0.783582 |

This preserves the action-level history signal from M112 while greatly
improving physical-pair diversity.

## Decision

M118 is positive as a fresh corpus gate.

It does not prove outcome-level self-identification yet. It does prove that the
project should stop using the exhausted M113/M115 corpus and repeat outcome and
boundary gates on this source-diverse corpus.

Next task: M119 should run M113-style continuation outcomes and M115/M116-style
boundary/robustness gates on the M118 corpus.
