# M1454 Paper-Route Source-Step Replay Boundary Retarget Design

## Summary

M1454 designs a normal-viable near-boundary retarget route after M1452 replay
produced zero history-positive rows.

Decision:

```text
source_step_replay_boundary_retarget_design_route_to_branch_synthesis
```

M1454 does not run replay, train, run PPO, promote, use private holdout, export
corpus, or change actor inputs.

## Diagnostic Basis

M1452 replay groups:

```text
selected groups: 64
normal_success groups: 24
normal_failed groups: 40
history_positive_rows: 0
control_positive_rows: 0
```

Normal-success margin distribution:

```text
min: 0.797596
p50: 4.627020
max: 5.494914
normal_success rows with margin <= 0.5: 0
normal_success rows with margin <= 1.0: 5
normal_success rows with margin <= 2.0: 12
```

This means M1452 is mostly split between:

```text
too hard: normal history already fails or is not valid;
too easy: normal history succeeds with large margin.
```

It is not yet centered on the terminal boundary where history variants can
cause success drops or meaningful margin gaps.

## Design Goal

Build a no-replay retarget proposal generator that consumes:

```text
runs/m1450_source_step_preflight_rerun/selected_candidate_rows.csv
runs/m1452_source_step_bounded_replay_smoke/actual_replay_rows.csv
```

and emits a smaller candidate set for another source-step preflight/replay
cycle.

The generator should not train or mutate actor state. It only changes replay
pressure proposals.

## Row Classification

Group M1452 rows by selected candidate and relocation key. For each group,
classify the normal branch:

```text
normal_boundary:
  normal_success == true and 0.0 <= normal_margin <= 1.0

too_easy:
  normal_success == true and normal_margin > 1.0

too_hard:
  normal_success == false or normal_margin < 0.0
```

The first rerun should prioritize:

```text
normal_boundary rows first;
too_easy rows with pressure increased;
too_hard rows with pressure relaxed;
```

## Retarget Controls

For `too_easy` rows, increase obstacle pressure conservatively:

```text
decrease body_longitudinal_offset by 1.0 or 2.0 when unclipped;
increase half_width_inflation by 0.2 or 0.4;
shift body_lateral_offset toward ego center by 0.2 or 0.4.
```

For `too_hard` rows, relax pressure:

```text
increase body_longitudinal_offset by 2.0 or 4.0;
decrease half_width_inflation by 0.2 when safe;
shift body_lateral_offset away from ego center by 0.2 or 0.4.
```

For existing `normal_boundary` rows, use local perturbations around the current
relocation:

```text
body_longitudinal_offset: -1.0, 0.0, +1.0
body_lateral_offset: -0.2, 0.0, +0.2 around current
half_width_inflation: 0.0, +0.2 around current
```

All proposals must remain source-step anchored:

```text
candidate_step_column: source_step
```

## Selection Gate

The implementation should export:

```text
retarget_candidate_rows.csv
retarget_rejected_rows.csv
retarget_summary.json
```

Preflight/replay rerun is admissible only if:

```text
retarget_candidate_rows >= 64
unique_source_seeds >= 4
unique_capability_pairs >= 6
unique_variants >= 2
candidate_step_column == source_step
training_started == false
replay_started == false
```

## Guardrails

M1454 guardrail status:

```text
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

## Synthesis Boundary

The current branch has reached the workflow synthesis cadence. M1454 therefore
does not route directly to implementation. It routes to branch synthesis first:

```text
m1455-paper-route-forward-source-preflight-validation-branch-synthesis
```
