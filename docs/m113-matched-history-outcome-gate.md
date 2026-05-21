# M113 Matched History Outcome Gate

## Question

M112 showed that reset, delayed, zeroed, and wrong matched histories change the
first action on M111 matched-current-response pairs. M113 asks whether those
action changes matter after rollout:

```text
Does normal history produce better continuation outcome than reset, delayed,
zero-current, zero-action, or wrong matched history?
```

This is the required bridge from action sensitivity to driver-level
self-identification evidence.

## Harness

Added:

```text
src/autodrift/matched_history_outcome_gate.py
tests/test_matched_history_outcome_gate.py
```

The harness reconstructs the same matched snapshots as M112, deep-copies the
environment at the left snapshot, and replays continuation variants:

```text
normal
reset_hidden
wrong_matched_history
delayed_history
zero_current_response
zero_action_history
```

It records success, collision, obstacle completion, return, first-action
distance, action-trajectory distance, and clearance margin. The actor contract
is unchanged.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_outcome_gate \
  --checkpoint-policy m62=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m102=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m105=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --pairs-csv runs/m111_matched_current_response_ambiguity_seed9510/matched_pairs.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 40 \
  --device cpu \
  --run-dir runs/m113_matched_history_outcome_gate_seed9510
```

Artifacts:

```text
runs/m113_matched_history_outcome_gate_seed9510/summary.json
runs/m113_matched_history_outcome_gate_seed9510/outcome_interventions.csv
runs/m113_matched_history_outcome_gate_seed9510/outcome_summary.csv
```

Top-level result:

```text
input_pair_count: 360
outcome_row_count: 2160
outcome_summary_rows: 54
```

## Aggregate Readout

| variant | pairs | success drop rate | normal-better fraction | mean margin gap | mean first-action distance | mean trajectory distance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| reset_hidden | 360 | 0.000 | 0.158 | 0.01098 | 0.506 | 0.614 |
| zero_current_response | 360 | 0.000 | 0.244 | 0.01113 | 0.114 | 0.339 |
| delayed_history | 360 | 0.000 | 0.006 | -0.00034 | 0.077 | 0.045 |
| wrong_matched_history | 360 | 0.000 | 0.000 | 0.00045 | 0.056 | 0.031 |
| zero_action_history | 360 | 0.000 | 0.017 | 0.00057 | 0.028 | 0.078 |

By checkpoint, the strongest margin effects are still small:

| checkpoint | variant | normal-better fraction | mean margin gap |
| --- | --- | ---: | ---: |
| M102 | zero_current_response | 0.308 | 0.01414 |
| M102 | reset_hidden | 0.167 | 0.01366 |
| M105 | zero_current_response | 0.408 | 0.01717 |
| M105 | reset_hidden | 0.308 | 0.01772 |
| M62 | zero_current_response | 0.017 | 0.00209 |
| M62 | reset_hidden | 0.000 | 0.00157 |

## Interpretation

M113 is negative for outcome-level self-identification.

The action-level signal from M112 is real: reset and zero-current variants have
large first-action and trajectory distances. But on this continuation surface:

- no variant produces success drops;
- wrong matched history does not reduce outcome;
- delayed history is outcome-neutral;
- reset and zero-current response create only small average clearance-margin
  gaps;
- M62 is almost completely outcome-neutral under these interventions.

The M111/M112 surface is therefore useful for action diagnostics but not yet a
training surface for safety outcomes.

## Decision

Status: completed, negative outcome gate.

Do not train another objective on M111 pairs as-is. The next proof surface must
be outcome-critical by construction, for example:

```text
matched current response
+ low normal clearance margin
+ wrong/reset history margin loss
+ obstacle geometry near the policy's boundary
```

Next task: M114 should mine or construct near-boundary matched-history outcome
pairs before another PPO or objective run.
