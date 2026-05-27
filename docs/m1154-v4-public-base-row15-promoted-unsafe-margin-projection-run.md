# M1154 V4 Public Base Row15 Promoted Unsafe-Margin Projection Run

## Purpose

M1154 runs the no-training promoted unsafe-margin projection probe designed in
M1152 and implemented in M1153.

It interpolates between:

```text
base:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt

target direction:
  runs/m1147_row15_promoted_actor_coupling_anchor100_s10_lr5e5_seed114602/optimized_checkpoint.pt
```

It evaluates exact M1144 objective, M1149 failed-row unsafe-margin retention,
and selected-alpha M1149 first replay. It does not train actor weights, run
PPO, mine rows, run M1061 family-intersection replay, run behavior gates,
promote, use private holdout, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.row15_promoted_unsafe_margin_projection_probe \
  --base-checkpoint runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --target-checkpoint runs/m1147_row15_promoted_actor_coupling_anchor100_s10_lr5e5_seed114602/optimized_checkpoint.pt \
  --snippet-npz runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz \
  --failed-rows-csv runs/m1149_row15_promoted_actor_update_first_replay/lost_success_drop_rows.csv \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --alphas 0.0,0.005,0.01,0.02,0.03,0.04,0.05,0.075,0.1,0.125,0.15,0.2,0.25,0.3,0.4,0.5,0.75,1.0 \
  --max-continuation-steps 60 \
  --logprob-margin 0.05 \
  --device cpu \
  --run-dir runs/m1154_row15_promoted_unsafe_margin_projection_probe
```

## Result

M1154 finds a nonzero projection candidate:

```text
result_class: row15_promoted_unsafe_margin_projection_first_replay_candidate
projection_candidate_pass_count: 6
selected_alpha: 0.05
selected_policy: alpha_0_05
selected_checkpoint:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
first_replay_pass: true
failure_types: none
```

No actor training, PPO, mining, M1061 family-intersection replay, full public
gate, fresh/OOD, behavior gate, promotion, private holdout, or actor-input
change occurred.

## Exact Objective

Selected alpha `0.05` improves exact M1144:

```text
alpha_0 exact M1144 loss:    0.417700
alpha_0_05 exact M1144 loss: 0.417322
delta:                      -0.000378
```

Exact objective continues improving at larger alphas, but those alphas fail
the failed-row unsafe-margin screen.

## Failed-Row Unsafe-Margin Screen

The selected alpha passes all `76` M1149 failed rows:

```text
failed_row_count: 76
selected alpha pass count: 76
wrong_history_success_count: 0
```

Selected-alpha margin summary:

```text
m267_m264:
  rows: 1
  wrong_history_margin_max: -0.000260
  normal_margin_min:         0.006786

row15_promoted_materialized:
  rows: 75
  wrong_history_margin_max: -0.000000497
  normal_margin_min:         0.001050
```

The trust region is narrow:

```text
alpha_0_005 through alpha_0_05: 76 / 76 failed rows pass
alpha_0_075:                   74 / 76 pass
alpha_0_1:                     74 / 76 pass
alpha_1:                        0 / 76 pass
```

The selected alpha is therefore the largest pre-registered alpha that preserves
all failed-row unsafe outcomes while still improving exact M1144.

## First Replay

Selected alpha `0.05` passes the M1149 ten-surface first replay:

```text
m183_m168:                 16 / 16 success drops retained
m183_m170:                 17 / 17 success drops retained
m193_m189:                 14 / 14 success drops retained
m212_m204:                 17 / 17 success drops retained
m223_m219:                 17 / 17 success drops retained
m267_m264:                 17 / 17 success drops retained
current_m333_surface:      17 / 17 success drops retained
m314_continuity_surface:   17 / 17 success drops retained
m317_continuity_surface:   17 / 17 success drops retained
row15_promoted_materialized:
                             148 / 148 success drops retained
```

Aggregate first-replay deltas are small:

```text
normal_success_delta:        0.0 on every surface
wrong_history_success_delta: 0.0 on every surface
normal_margin_mean_delta:    about 0.000024 to 0.000028
margin_gap_mean_delta:       about -0.000008 to -0.000010
```

## Artifacts

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/summary.json
runs/m1154_row15_promoted_unsafe_margin_projection_probe/projection_candidates.csv
runs/m1154_row15_promoted_unsafe_margin_projection_probe/failed_row_gate_rows.csv
runs/m1154_row15_promoted_unsafe_margin_projection_probe/failed_row_replay_rows.csv
runs/m1154_row15_promoted_unsafe_margin_projection_probe/first_replay_summary.csv
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

## Interpretation

M1154 validates the M1152 hypothesis: the full M1147 actor update is too large,
but a small nonzero projection along the same direction can preserve the M1149
wrong-history unsafe proof rows while retaining exact M1144 improvement.

This is still not promotable. The selected alpha has only passed exact M1144,
failed-row unsafe screening, and M1149 first replay. It has not passed M1061
family-intersection replay, behavior diagnostics, fresh/OOD, full public gate,
private holdout, or PPO stability.

The row15-promoted materialized wrong-history margin at selected alpha is very
close to zero (`-4.97e-7` max), so the next gates should be treated as proof
diagnostics, not promotion evidence.

## Decision

```text
decision: row15_promoted_unsafe_margin_projection_first_replay_candidate_route_to_family_behavior_design
next: m1155-v4-public-base-row15-promoted-projection-family-behavior-design
```
