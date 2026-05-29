# M1415 Paper-Route Clear Near-Boundary Warmup Retarget Source Smoke

## Summary

M1415 attempted the retargeted staged warmup source smoke designed by M1414.

Decision:

```text
clear_near_boundary_retarget_source_sampling_failed_route_to_sampling_repair
```

M1415 does not run outcome interventions, train, run PPO, promote, use private
holdout, export a training corpus, or change actor inputs.

## Command

The full 64-seed attempt was started but did not produce output in a reasonable
time because the retargeted obstacle filter repeatedly entered slow sampling
failure paths. It was stopped and not counted as a completed 64-seed result.

The completed failure artifact is a 2-seed preflight written to the formal
M1415 run directory:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.warmup_latched_config_smoke \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1415_clear_near_boundary_warmup_retarget_source_wave.json \
  --seed-start 141500 \
  --seed-count 2 \
  --reveal-steps 48,56,64,72 \
  --history-length 56 \
  --min-warmup-evidence-steps 16 \
  --max-source-rows 256 \
  --device cpu \
  --run-dir runs/m1415_clear_near_boundary_warmup_retarget_source_smoke
```

## Result

```text
result_class: warmup_latched_no_rows
source_rows: 0
matched_current_rows: 0
bucketed_current_rows: 0
matched_or_bucketed_reveal_rows: 0
finite_metric_rows: 0
rejected_rows: 272
actor_parameters_changed: false
```

Rejected-row reasons:

```text
trace_reconstruction_failed: 236
preferred_fault_insufficient_warmup_evidence: 22
wrong_fault_insufficient_warmup_evidence: 14
```

Most explicit trace errors are obstacle sampling failures:

```text
failed to sample an obstacle scenario matching the configured filters: 118
```

Other failures are downstream trace reconstruction failures after scenario or
termination problems. No source rows were materialized, so warmup gate evidence
and collision-share gates cannot be evaluated.

## Interpretation

M1415 fails before testing the retuned warmup gate. The near-boundary obstacle
filter in the M1414 design is too strict when combined with the staged warmup
retarget:

```text
obstacle.distance_range: [4.0, 18.0]
obstacle.half_width_range: [1.00, 1.75]
obstacle.max_threshold_score: 0.45
```

This should be classified as:

```text
scenario_sampling_failure
```

It is not evidence that the retuned warmup gate lacks command-response signal.
The source smoke never got far enough to test that.

## Next

M1416 should design a sampling repair that relaxes only the obstacle sampling
filter while preserving the retuned warmup gate geometry.

Candidate repair:

```text
keep warmup_gate:
  distance_range: [10.0, 18.0]
  lateral_offset_range: [-2.2, 2.2]
  half_width_range: [0.25, 0.45]
  reveal_step: 2
  max_active_steps: 44

restore obstacle pressure closer to M1410:
  distance_range: [4.0, 20.0]
  half_width_range: [0.90, 1.65]
  max_threshold_score: 0.50
```

M1416 should not run source smoke. It should write a repair design and then
admit one repaired source smoke only if the design keeps the no-training and
no-claim-expansion guardrails.
