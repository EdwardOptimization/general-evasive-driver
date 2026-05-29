# M1414 Paper-Route Clear Near-Boundary Warmup Retarget Design

## Summary

M1414 designs the next retargeted staged warmup experiment after M1412 produced
sparse but non-collision-only warmup-history positives.

Decision:

```text
clear_near_boundary_warmup_retarget_design_admit_source_smoke
```

M1414 does not run source smoke, run outcome interventions, train, run PPO,
promote, use private holdout, export a training corpus, or change actor inputs.

## Design Goal

M1412 showed that staged warmup can create sparse outcome-relevant history
effects, but the distribution is not yet good enough:

```text
warmup_history_positive_rows: 14
accepted_history_unique_source_seeds: 3
preferred near-boundary accepted-history rows: 2 from 1 seed
wrong-warmup positives: 0
```

The next experiment should not optimize those three accepted seeds. It should
shift the task distribution toward:

```text
clear or low-invasiveness warmup source rows;
preferred/broad near-boundary emergency outcomes;
source-diverse seed/fault/reveal coverage;
wrong-warmup variants as first-class diagnostics.
```

## Retarget Strategy

M1415 should run source smoke only. It should retune the warmup gate to reduce
collision pressure while preserving command-response stimulus:

```text
warmup_gate.distance_range:       [10.0, 18.0]
warmup_gate.lateral_offset_range: [-2.2, 2.2]
warmup_gate.half_width_range:     [0.25, 0.45]
warmup_gate.reveal_step:          2
warmup_gate.max_active_steps:     44
warmup_gate.finish_pass_distance: 1.5
```

Compared with M1410:

```text
distance moves slightly later;
half-width narrows;
lateral range widens;
max active steps remain short enough to reveal the emergency obstacle after warmup.
```

This should lower gate collision pressure while keeping visible obstacle-slot
stimulus in the warmup history.

Emergency obstacle pressure should remain near-boundary:

```text
track_kind: figure_eight
track_radius: 75.0
track_width: 6.8
obstacle.distance_range: [4.0, 18.0]
obstacle.half_width_range: [1.00, 1.75]
obstacle.max_threshold_score: 0.45
obstacle.perception_reveal_distance: 6.0
```

The source smoke should use fresh public seeds:

```text
seed_start: 141500
seed_count: 64
reveal_steps: 48,56,64,72
history_length: 56
min_warmup_evidence_steps: 16
```

## Source-Smoke Gates

M1415 should pass structurally only if it meets all of:

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
clear + clear_low_margin matched/bucketed rows >= 120 after source diagnostics
```

If the collision share remains above `0.50`, M1415 should route to a gate
parameter retune before outcome probing.

## Outcome-Probe Gates for Later

M1415 must not run outcome probing. If M1415 source smoke passes, the follow-up
outcome probe should require:

```text
normal_margin_candidate_rows >= 180
broad_near_boundary_candidate_rows >= 60
preferred_near_boundary_candidate_rows >= 35
warmup_history_positive_rows >= 24 for a useful public repeat
accepted_history_unique_source_seeds >= 6
accepted_history_unique_capability_pairs >= 6
accepted_history_unique_reveal_buckets >= 4
wrong_warmup_history_same_reveal_positive_rows > 0 or same_recent_wrong_warmup_history_positive_rows > 0 for wrong-history evidence
```

This is not the final public-positive threshold; it is a retarget-repeat bar.
Training/corpus export remains blocked until a later source-diverse outcome
result passes the stronger public-positive standard.

## Overfit Controls

M1415 must not:

```text
reuse only M1412 accepted seeds;
select candidate rows from accepted-history rows;
change actor input contract;
use hidden parameters or oracle labels as actor input;
use private holdout;
train or run PPO;
export a corpus;
promote a checkpoint;
claim level3 self-identification.
```

M1415 should report:

```text
source diversity;
matched/bucketed diversity;
warmup response/action history L2;
warmup gate collision share;
clear/clear_low/collision source strata;
reveal-step split;
capability-pair split.
```

## Next

Next milestone:

```text
m1415-paper-route-clear-near-boundary-warmup-retarget-source-smoke
```

M1415 is admitted as no-training source smoke only.
