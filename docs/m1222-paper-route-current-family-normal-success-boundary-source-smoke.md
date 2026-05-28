# M1222 Paper-Route Current-Family Normal-Success Boundary Source Smoke

## Summary

M1222 runs the current-family normal-success boundary source miner selected by
M1221. It tests whether a broader source window can produce real wrong-history
action/outcome-critical rows that M1217 missed.

Decision:

```text
normal_success_boundary_source_negative_admit_audit
```

Failure classification:

```text
near_boundary_action_gap_but_no_outcome_gap
```

No training, PPO, actor update, checkpoint repair, promotion, private holdout,
profile tuning, or actor-input change occurs in M1222.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.normal_success_boundary_source_miner \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --surface-config l3_current=configs/paper_route_corrected_profiles/m1207_l3_online_gru.json \
  --surface-seed-range l3_current=122700:122763 \
  --sequence-lengths 5,7,9 \
  --obstacle-distance-min 0.0 \
  --obstacle-distance-max 45.0 \
  --normal-margin-min 0.0 \
  --normal-margin-max 1.0 \
  --max-right-candidates-per-left 96 \
  --max-candidate-pairs-per-surface 2400 \
  --context-distance-threshold 0.25 \
  --response-distance-threshold 0.20 \
  --obstacle-x-abs-delta 10.0 \
  --obstacle-y-abs-delta 2.0 \
  --step-abs-delta 30 \
  --min-wrong-first-action-l2 0.002 \
  --min-wrong-action-sequence-mean-l2 0.006 \
  --min-preferred-rejected-action-mean-l2 0.010 \
  --min-margin-gap 0.010 \
  --max-snapshots-per-surface 768 \
  --max-snapshots-per-seed 8 \
  --sample-stride 3 \
  --max-continuation-steps 12 \
  --device cpu \
  --run-dir runs/m1222_current_family_normal_success_boundary_source_smoke
```

## Artifacts

```text
runs/m1222_current_family_normal_success_boundary_source_smoke/summary.json
runs/m1222_current_family_normal_success_boundary_source_smoke/snapshot_bank_summary.csv
runs/m1222_current_family_normal_success_boundary_source_smoke/normal_window_summary.csv
runs/m1222_current_family_normal_success_boundary_source_smoke/normal_window_rows.csv
runs/m1222_current_family_normal_success_boundary_source_smoke/candidate_scores.csv
runs/m1222_current_family_normal_success_boundary_source_smoke/normal_success_boundary_rows.csv
runs/m1222_current_family_normal_success_boundary_source_smoke/normal_success_boundary_corpus.npz
```

## Run Result

```text
corpus_passed: false
accepted_rows: 0
```

High-level counts:

```text
snapshot_count:             512
candidate_pairs:           2400
candidate_rows:            7200
accepted_rows:                0
actor_parameters_changed: false
actor_checkpoint_written:  false
ppo_used:                  false
```

Actor checksum was unchanged:

```text
c2f1998fdca8f61a4fa2e2d2c6522561adfb00e486bd43d1ebc4fff12ec076fc
```

## Normal Window Coverage

M1222 is not blocked by missing normal-success boundary windows:

```text
near_boundary_preferred: 45
early_safe_diagnostic:  350
already_failed:         117
```

Normal window summary:

| Window Class | Rows | Seeds | Targets | Normal Margin Mean | Obstacle Distance Mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| `near_boundary_preferred` | `45` | `36` | `3` | `0.499979` | `4.741778` |
| `early_safe_diagnostic` | `350` | `64` | `3` | `6.476335` | `11.411644` |
| `already_failed_diagnostic` | `117` | `60` | `3` | `-0.110395` | `2.990791` |

Near-boundary preferred windows:

```text
normal_margin_min:  0.022122
normal_margin_mean: 0.499979
normal_margin_max:  0.951090
targets: drift_required=22, unavoidable=21, aes_feasible=2
```

The near-boundary count barely passes the `>= 40` window-coverage threshold,
but it is enough to classify the next failure mode.

## Wrong-History Candidate Result

All candidate normal and wrong branches succeeded:

```text
candidate_normal_success_rate: 1.000
candidate_wrong_success_rate:  1.000
success_drop_rows:             0
```

Action thresholds:

```text
wrong_first_action_l2 >= 0.002 rows:              6927
wrong_action_sequence_mean_l2 >= 0.006 rows:       707
preferred/rejected action mean_l2 >= 0.010 rows:   274
all action thresholds rows:                        274
```

Outcome threshold:

```text
margin_gap >= 0.010 rows: 0
max margin_gap:           0.002370
mean margin_gap:         -0.000115
```

The strongest action-divergent subset is source-diverse enough to be meaningful
as a diagnostic, but not outcome-critical:

```text
all-action-threshold rows: 274
physical pairs:             85
left seeds:                  7
right seeds:                24
targets: unavoidable=176, drift_required=98
mean action sequence L2:     0.024635
max action sequence L2:      0.034728
mean margin gap:            -0.000157
max margin gap:              0.002370
```

## Interpretation

M1222 improves the evidence state relative to M1217/M1220:

```text
M1217/M1220: current-family matched histories are mostly action-equivalent.
M1222: a broader normal-success source can find sustained action divergence.
```

But it still does not produce causal-history outcome evidence:

```text
wrong-history action can change,
but the scene remains too safe or too outcome-insensitive for margin/success
degradation under these compatible wrong histories.
```

This is not `no_near_boundary_normal_success_windows`:

```text
near_boundary_preferred_snapshots = 45
```

This is not `near_boundary_exists_but_no_action_gap`:

```text
all_action_threshold_rows = 274
```

It is:

```text
near_boundary_action_gap_but_no_outcome_gap
```

## Rejected Shortcuts

Do not:

- train from the empty accepted corpus;
- lower `min_margin_gap` inside this result;
- use the 274 action-divergent rows as self-ID proof;
- promote any checkpoint;
- run PPO;
- claim history necessity or recurrent belief from this source mining result.

## Selected Next Route

The next step should be an audit, not another immediate mining run.

M1223 should decide whether the next branch should:

1. relocate/perturb the action-divergent M1222 rows toward a terminal boundary;
2. extend the outcome horizon or terminal-margin scoring;
3. move to stronger cross-family or explicit fault source distributions;
4. synthesize the causal-history branch before adding more narrow milestones.

## Decision

```text
normal_success_boundary_source_negative_admit_audit
```

Next blocker:

```text
m1223-paper-route-current-family-boundary-source-negative-audit
```
