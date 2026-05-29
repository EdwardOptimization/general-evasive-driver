# M1416 Paper-Route Warmup Retarget Sampling Repair Design

## Summary

M1416 designs a repair for the M1415 no-row source smoke. M1415 failed before
testing the retuned warmup gate because the obstacle scenario filter was too
strict.

Decision:

```text
warmup_retarget_sampling_repair_design_admit_repaired_source_smoke
```

M1416 does not run source smoke, outcome interventions, training, PPO,
promotion, private holdout, corpus export, or actor-input changes.

## Failure Cause

M1415 result:

```text
result_class: warmup_latched_no_rows
source_rows: 0
rejected_rows: 272
trace_reconstruction_failed: 236
dominant_error: failed to sample an obstacle scenario matching the configured filters
```

The failure is classified as:

```text
scenario_sampling_failure
```

It should not be interpreted as evidence against staged warmup or the retuned
warmup gate, because no source rows were produced.

## Repair

The repair should preserve the M1415 retuned warmup gate:

```text
warmup_gate.distance_range:       [10.0, 18.0]
warmup_gate.lateral_offset_range: [-2.2, 2.2]
warmup_gate.half_width_range:     [0.25, 0.45]
warmup_gate.reveal_step:          2
warmup_gate.max_active_steps:     44
warmup_gate.finish_pass_distance: 1.5
```

It should relax the obstacle filter back toward the M1410 proven-sampleable
settings:

```text
obstacle.distance_range:     [4.0, 20.0]
obstacle.half_width_range:   [0.90, 1.65]
obstacle.max_threshold_score: 0.50
```

This isolates the question:

```text
Does the retuned warmup gate reduce collision pressure while keeping source
materialization, if obstacle sampling is not over-constrained?
```

## Repaired Source Smoke

M1417 should run source smoke only:

```text
seed_start: 141700
seed_count: 48
reveal_steps: 48,56,64,72
history_length: 56
min_warmup_evidence_steps: 16
max_source_rows: 6144
```

The source structural gates are:

```text
source_rows >= 1024
matched_or_bucketed_reveal_rows >= 240
matched/bucketed unique_source_seeds >= 28
matched/bucketed unique_capability_pairs >= 12
matched/bucketed unique_reveal_buckets >= 64
finite_metric_rows == source_rows
actor_parameters_changed == false
```

Warmup evidence gates:

```text
matched/bucketed warmup_gate_visible_rows == matched_or_bucketed_reveal_rows
matched/bucketed warmup_evidence_rows == matched_or_bucketed_reveal_rows
matched/bucketed warmup_response_history_l2_p95 >= 0.035
matched/bucketed warmup_action_history_l2_p95 >= 0.008
```

Invasiveness gates:

```text
matched/bucketed warmup_gate_collision_share <= 0.50
clear + clear_low_margin matched/bucketed rows >= 120
```

## Next

Next milestone:

```text
m1417-paper-route-warmup-retarget-sampling-repair-source-smoke
```

M1417 must not run outcome interventions, train, run PPO, promote, use private
holdout, export a corpus, change actor inputs, or claim self-identification from
source materialization.
