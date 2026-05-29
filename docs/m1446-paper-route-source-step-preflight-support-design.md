# M1446 Paper-Route Source-Step Preflight Support Design

## Summary

M1446 designs the missing source-step support exposed by M1445.

Decision:

```text
source_step_preflight_support_design_admit_implementation
```

M1446 does not run preflight, bounded replay, outcome interventions, training,
PPO, promotion, private holdout, corpus export, or actor-input changes.

## Problem

M1445 selected a valid forward candidate pool from source-step rows:

```text
selected_candidate_rows: 128
source_body_x_min: 5.065734
relocation_clipped_share: 0.0
```

But the existing preflight/replay tool reconstructs traces using `reveal_step`.
For M1445, that would reintroduce the old timing problem: the row is valid at
`source_step`, while `reveal_step` can be too late or too close.

The next preflight/replay layer must preserve the temporal anchor selected by
the source pipeline.

## Design

Add an explicit candidate step column to the bounded relocation replay probe:

```text
--candidate-step-column reveal_step
--candidate-step-column source_step
```

Default:

```text
reveal_step
```

The default preserves all previous M1435/M1429 behavior. The M1445 follow-up
should use:

```text
--candidate-step-column source_step
```

The implementation should route the selected column through:

```text
run_geometry_preflight_only_probe
geometry_preflight_from_trace_candidates
run_bounded_relocation_replay_probe
actual bounded replay trace reconstruction
artifact rows and summaries
```

## Required Behavior

For every selected candidate, the tool should write both:

```text
reveal_step
candidate_step
candidate_step_column
```

If `source_step` is used, it must not mutate or overwrite `reveal_step`.

Replay outputs should keep the original `reveal_step` for lineage and add
`candidate_step` for the actual trace/replay anchor.

## Tests

Focused tests should cover:

```text
1. preflight source-step column is passed to trace_for instead of reveal_step
2. replay source-step column is passed to both preferred and wrong trace_for
3. default candidate step column remains reveal_step
4. missing candidate step column raises a clear error
```

These tests should use lightweight monkeypatched trace helpers rather than a
full policy rollout.

## Guardrails

The implementation must not:

```text
change actor inputs
change actor weights
train or run PPO
run bounded replay as part of implementation
export a training corpus
promote a checkpoint
claim self-identification evidence
```

## Next Route

Admit:

```text
m1447-paper-route-source-step-preflight-support-implementation
```

M1447 should implement the candidate-step column support and focused tests only.
