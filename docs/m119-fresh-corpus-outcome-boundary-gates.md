# M119 Fresh-Corpus Outcome And Boundary Gates

M118 restored source diversity at the matched-current/action-intervention level:
`471` matched rows across `155` physical pairs and `408` wrong-history action
rows across `140` physical pairs. M119 tests whether that broader action signal
actually becomes outcome-level self-identification evidence.

## Question

```text
Does the M118 source-diverse corpus produce normal-history safety outcomes that
are measurably better than wrong, reset, delayed, zero-current, or zero-action
history continuations?
```

If the passive continuation outcome is still weak, M119 also repeats the
M115/M116 boundary-tightening path on the fresh corpus.

## Outcome Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.matched_history_outcome_gate \
  --checkpoint-policy m62=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m102=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m105=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --pairs-csv runs/m118_source_diverse_matched_current_seed9510/matched_pairs.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 80 \
  --device cpu \
  --run-dir runs/m119_fresh_corpus_outcome_gate_seed9510
```

Artifacts:

```text
runs/m119_fresh_corpus_outcome_gate_seed9510/summary.json
runs/m119_fresh_corpus_outcome_gate_seed9510/outcome_interventions.csv
runs/m119_fresh_corpus_outcome_gate_seed9510/outcome_summary.csv
```

Top-level result:

| Metric | Value |
| --- | ---: |
| Input pairs | 408 |
| Outcome rows | 2448 |
| Summary rows | 54 |

Aggregate intervention readout:

| Variant | Rows | Physical pairs | Success drops | Normal-better fraction | Mean margin gap | P90 margin gap | Mean first-action distance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wrong matched history | 408 | 140 | 0 | 0.000 | 0.000165 | 0.002561 | 0.066306 |
| reset hidden | 408 | 140 | 0 | 0.127 | 0.009007 | 0.022325 | 0.518639 |
| zero current response | 408 | 140 | 0 | 0.196 | 0.009643 | 0.033238 | 0.124691 |
| zero action history | 408 | 140 | 0 | 0.005 | -0.000043 | 0.003132 | 0.034049 |
| delayed history | 408 | 140 | 0 | 0.005 | 0.000256 | 0.002595 | 0.105105 |

Wrong-history by checkpoint and target:

| Checkpoint | Target | Rows | Physical pairs | Success drops | Mean margin gap | Mean action distance |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| M102 | braking | 80 | 62 | 0 | 0.000651 | 0.058956 |
| M102 | lateral | 31 | 22 | 0 | -0.001146 | 0.087129 |
| M102 | yaw | 27 | 15 | 0 | 0.001735 | 0.075587 |
| M105 | braking | 80 | 60 | 0 | 0.000675 | 0.055161 |
| M105 | lateral | 31 | 22 | 0 | -0.001134 | 0.088959 |
| M105 | yaw | 23 | 13 | 0 | 0.001796 | 0.081434 |
| M62 | braking | 80 | 62 | 0 | -0.000247 | 0.067883 |
| M62 | lateral | 35 | 28 | 0 | -0.001152 | 0.065487 |
| M62 | yaw | 21 | 11 | 0 | 0.000185 | 0.039452 |

Passive outcome result: negative. The fresh corpus preserves wrong-history
action differences, but those differences do not produce success drops or
meaningful wrong-history clearance degradation.

## Boundary Commands

M119 then runs boundary tightening around the fresh outcome rows. The first pass
uses a capped candidate set:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy m62=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m102=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m105=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --outcome-csv runs/m119_fresh_corpus_outcome_gate_seed9510/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-pairs-per-checkpoint-target 20 \
  --min-base-action-distance 0.02 \
  --target-normal-margins 0.005,0.01,0.02,0.05,0.10,0.15 \
  --half-width-inflations 0 \
  --min-margin-gap 0.02 \
  --min-accepted-wrong-rows 10 \
  --report-variants wrong_matched_history,reset_hidden,zero_current_response,zero_action_history,delayed_history \
  --device cpu \
  --run-dir runs/m119_fresh_corpus_boundary_relocation_seed9510
```

Because this failed the row-count gate, M119 also runs an all-candidate
diagnostic to rule out a candidate-cap artifact:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy m62=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m102=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m105=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --outcome-csv runs/m119_fresh_corpus_outcome_gate_seed9510/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-pairs-per-checkpoint-target 0 \
  --min-base-action-distance 0.02 \
  --target-normal-margins 0.005,0.01,0.02,0.05,0.10,0.15 \
  --half-width-inflations 0 \
  --min-margin-gap 0.02 \
  --min-accepted-wrong-rows 10 \
  --report-variants wrong_matched_history,reset_hidden,zero_current_response,zero_action_history,delayed_history \
  --device cpu \
  --run-dir runs/m119_fresh_corpus_boundary_all_candidates_seed9510
```

The all-candidate boundary rows are then checked with the M116-style robustness
gate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_wrong_history_surface_robustness \
  --boundary-rows-csv runs/m119_fresh_corpus_boundary_all_candidates_seed9510/boundary_relocation_rows.csv \
  --control-checkpoint-label m62 \
  --margin-bucket-width 0.01 \
  --min-accepted-wrong-rows 10 \
  --min-physical-pairs 6 \
  --min-left-steps 5 \
  --min-checkpoints 2 \
  --min-targets 3 \
  --min-margin-buckets 2 \
  --min-success-drop-fraction 1.0 \
  --max-rows-per-pair-fraction 0.40 \
  --max-control-accepted-rows 0 \
  --run-dir runs/m119_fresh_corpus_boundary_all_candidates_robustness_seed9510
```

## Boundary Result

| Boundary pass | Candidates | Rows | Accepted wrong rows | Accepted wrong pairs | Accepted reset rows | Accepted zero-current rows | Surface found |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| capped candidates | 171 | 5630 | 6 | 4 | 293 | 244 | false |
| all candidates | 315 | 8720 | 6 | 4 | 371 | 298 | false |

All-candidate robustness metrics:

| Metric | Value |
| --- | ---: |
| Accepted wrong rows | 6 |
| Accepted physical pairs | 3 |
| Accepted left steps | 3 |
| Accepted checkpoints | 2 |
| Accepted targets | 2 |
| Accepted normal-margin buckets | 1 |
| Success-drop fraction | 1.0 |
| Max rows per physical pair fraction | 0.333 |
| M62 accepted wrong rows | 0 |
| Mean accepted wrong margin gap | 0.007403 |
| Max accepted wrong margin gap | 0.008809 |
| Mean accepted normal margin | 0.006483 |

Robustness decision:

```text
reject_duplicate_dominated_boundary_surface
```

Failed gates:

| Gate | Observed | Required |
| --- | ---: | ---: |
| accepted wrong rows | 6 | >= 10 |
| accepted physical pairs | 3 | >= 6 |
| accepted left steps | 3 | >= 5 |
| accepted targets | 2 | >= 3 |
| accepted normal-margin buckets | 1 | >= 2 |

Accepted physical-pair summary:

| Physical pair | Rows | Checkpoints | Targets | Bucket |
| --- | ---: | --- | --- | --- |
| `9530:18:9540:21` | 2 | M102,M105 | lateral | 0.000-0.010 |
| `9530:21:9540:27` | 2 | M102,M105 | braking | 0.000-0.010 |
| `9530:24:9540:30` | 2 | M102,M105 | braking | 0.000-0.010 |

## Interpretation

M119 is negative for robust outcome-level self-identification.

The important finding is not just that the gate fails. It is that a fresh,
source-diverse matched-current/action corpus still collapses to the same old
`9530/9540` outcome-critical boundary rows when safety outcome is required.
This means the current matched-current-response mining objective is good for
finding action-level ambiguity but is not sufficient for finding outcome-critical
self-identification cases.

Do not train a boundary-aware wrong-history objective from M119.

The next step should move upstream again, but this time mine directly for
outcome-critical and source-diverse cases instead of mining matched-current
action ambiguity first and hoping outcome sensitivity appears later.
