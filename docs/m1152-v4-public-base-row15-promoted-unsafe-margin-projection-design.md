# M1152 V4 Public Base Row15 Promoted Unsafe-Margin Projection Design

## Purpose

M1152 designs the next repair after M1151 closed the
`row15_promoted_target_materialization` branch and opened
`row15_promoted_unsafe_margin_projection`.

This milestone is design-only. It does not train actor weights, run PPO, run
replay, mine rows, promote a checkpoint, use private holdout, or change actor
inputs.

## Diagnosis To Preserve

M1150 established:

```text
M1149 failure type: proof_washout
mechanism: wrong-history-safe terminal-margin crossing
normal_lost_events: 0
wrong_history_safe_events: 76
materialized failed rows: 75
materialized failed unique geometries: 49
materialized failed geometries covered by M1144: true
m267 failure covered by M1144: false
```

The failed materialized rows are low-weight near-boundary braking rows:

```text
failed-row weight mean:    0.003962
nonfailed-row weight mean: 0.015196
failed wrong-history margin mean:    -0.000463
nonfailed wrong-history margin mean: -0.004114
```

Therefore the next repair should not be another generic actor update. The
missing condition is:

```text
under wrong history, failed rows must remain unsuccessful and terminal margin
must remain negative; under normal history, they must remain successful.
```

## Existing Tooling Gap

The old `autodrift.row15_unsafe_margin_projection_probe` is useful as a design
reference but should not be reused directly for this branch.

It is hardcoded for the M1120 row15 cliff:

```text
ROW15_SURFACES: fixed five old/source-diverse row15 corpora
FIRST_REPLAY_SURFACES: fixed six M1120 surfaces
row selector: row_id == 15 and physical_pair_key == 9530:21:9550:21
required anchors: M1115 target-base and combined trajectory anchor NPZ files
```

M1149 is different:

```text
failed rows: 76
surfaces: m267_m264 plus row15_promoted_materialized
materialized rows: 75 rows / 49 geometries / 9 physical pairs / 5 source labels
required first replay: all 10 M1149 surfaces
```

So the next milestone should implement a promoted-surface projection runner,
not force M1149 through the old row15-only probe.

## Proposed Runner

Implement a new runner:

```text
python -m autodrift.row15_promoted_unsafe_margin_projection_probe
```

Proposed inputs:

```text
--base-checkpoint
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt

--target-checkpoint
  runs/m1147_row15_promoted_actor_coupling_anchor100_s10_lr5e5_seed114602/optimized_checkpoint.pt

--snippet-npz
  runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz

--failed-rows-csv
  runs/m1149_row15_promoted_actor_update_first_replay/lost_success_drop_rows.csv

--env-config
  configs/m121_human_view_zero_obstacle_relvel.json

--alphas
  0.0,0.005,0.01,0.02,0.03,0.04,0.05,0.075,0.1,0.125,
  0.15,0.2,0.25,0.3,0.4,0.5,0.75,1.0

--max-continuation-steps
  60
```

The runner should interpolate:

```text
theta_alpha = theta_base + alpha * (theta_m1147_114602 - theta_base)
```

Because M1147 changed only actor-coupling tensors, every interpolated
checkpoint must still satisfy:

```text
changed parameter prefixes:
  actor_mean.
  response_context_fusion.0.
actor inputs changed: false
log_std changed: false
```

## Lexicographic Acceptance

### 1. Contract

For every alpha:

```text
actor inputs unchanged
parameter changes limited to actor_mean.* and response_context_fusion.0.*
log_std unchanged
```

Alpha `0.0` is baseline reference only. A selected candidate must be nonzero.

### 2. Exact M1144 Objective

Evaluate exact M1144 objective with:

```text
snippet_npz:
  runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz
logprob_margin: 0.05
```

Required for a selected alpha:

```text
exact M1144 loss <= base exact M1144 loss
exact M1144 loss < base exact M1144 loss
```

The second condition forces actual movement; alpha `0.0` cannot pass.

### 3. Failed-Row Unsafe-Margin Screen

Replay only the M1149 failed rows for all alpha candidates before any first
replay escalation.

For each failed row:

```text
normal_success == true
normal_margin >= 0.0
wrong_history_success == false
wrong_history_margin < 0.0
```

This deliberately uses a sign rule rather than a fixed `-0.00025` threshold:
some baseline M1149 wrong-history margins are only about `-0.000063`, so a
stricter fixed slack would reject the current public-gate base itself.

The candidate can pass only if all `76` M1149 lost success-drop rows retain
their success-drop relation.

### 4. Candidate Selection Before First Replay

Among nonzero alphas satisfying contract, exact M1144 improvement, and failed
row unsafe-margin retention, select the largest alpha for first replay.

Do not choose alpha based on first-replay outcome. If the selected alpha fails
first replay, the result is a failure audit, not trying another alpha inside
the same milestone.

### 5. First Replay

The selected alpha may run the M1149 first replay stack only:

```text
m183_m168
m183_m170
m193_m189
m212_m204
m223_m219
m267_m264
current_m333_surface
m314_continuity_surface
m317_continuity_surface
row15_promoted_materialized
```

Thresholds remain unchanged:

```text
max_continuation_steps: 60
max_normal_success_drop: 0.0
max_normal_margin_regression: 0.005
max_margin_gap_regression: 0.001
max_success_drop_count_regression: 0
```

M1153/M1154 must not proceed to M1061 family-intersection replay, full public
gate, fresh/OOD, behavior gates, PPO, promotion, or private holdout.

## Result Classes For The Future Run

If no nonzero alpha passes exact plus failed-row unsafe screening:

```text
result_class: row15_promoted_unsafe_margin_projection_no_candidate
next: terminal-margin objective design
```

If a nonzero alpha passes screening but selected-alpha first replay fails:

```text
result_class: row15_promoted_unsafe_margin_projection_first_replay_failed
next: row-level first-replay failure audit
```

If a nonzero alpha passes screening and first replay:

```text
result_class: row15_promoted_unsafe_margin_projection_first_replay_candidate
next: family-intersection and behavior diagnostic design only
```

No result from this projection branch is promotable by itself.

## Next Milestone

The immediate next step is implementation of the promoted projection runner,
not the projection run itself.

```text
decision: row15_promoted_unsafe_margin_projection_design_admit_runner_implementation
next: m1153-v4-public-base-row15-promoted-unsafe-margin-projection-runner-implementation
```
