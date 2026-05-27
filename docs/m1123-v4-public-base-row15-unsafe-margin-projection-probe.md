# M1123 V4 Public Base Row15 Unsafe-Margin Projection Probe

## Purpose

M1123 runs the no-training projection probe designed in M1122.

It interpolates between the current public base and M1118 seed `111800`, then
checks exact M1107, trajectory-anchor MSE, row15 unsafe-margin retention, and
the selected-alpha six-surface first replay. It does not train actor weights,
run PPO, run family-intersection replay, run full public gate, run fresh/OOD,
run behavior gates, promote, use private holdout, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.row15_unsafe_margin_projection_probe \
  --base-checkpoint runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --target-checkpoint runs/m1118_failed_wrong_history_retention_actor_update_seed111800/optimized_checkpoint.pt \
  --snippet-npz runs/m1107_materialized_objective_corpus/boundary_outcome_corpus.npz \
  --target-anchor-npz runs/m1115_materialized_failed_wrong_history_retention_export/target_base_rejected_trajectory_anchor.npz \
  --combined-anchor-npz runs/m1115_materialized_failed_wrong_history_retention_export/combined_target_base_rejected_anchor.npz \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --alphas 0.0,0.05,0.1,0.15,0.2,0.25,0.3,0.4,0.5,0.75,1.0 \
  --max-continuation-steps 60 \
  --logprob-margin 0.05 \
  --device cpu \
  --run-dir runs/m1123_row15_unsafe_margin_projection_probe
```

## Result

M1123 finds a nonzero first-replay candidate:

```text
result_class: row15_unsafe_margin_projection_first_replay_candidate
projection_candidate_pass_count: 3
selected_alpha: 0.15
selected_checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
first_replay_pass: true
failure_types: none
```

No actor training, PPO, family-intersection replay, full public gate,
fresh/OOD, behavior gate, promotion, private holdout, or actor-input change
occurred.

## Selected Candidate

Selected alpha `0.15`:

```text
exact M1107 delta vs base:         -0.000417471
target-base trajectory MSE:         0.0000000336
combined trajectory MSE:            0.0000050340
changed parameters:
  actor_mean.bias
  actor_mean.weight
  response_context_fusion.0.bias
  response_context_fusion.0.weight
actor inputs changed: false
```

The largest alpha that passes the registered projection gates is `0.15`.
Alphas `0.05`, `0.10`, and `0.15` pass. Alpha `0.20` and larger improve exact
M1107 more, but fail row15 unsafe-margin retention.

## Row15 Unsafe-Margin Gate

For selected alpha `0.15`, all five row15 variants pass:

```text
m223_m219:
  threshold: -0.001260438
  candidate wrong margin: -0.002252133

m267_m264:
  threshold: -0.000280990
  candidate wrong margin: -0.000293533

current_m333_surface:
  threshold: -0.000668505
  candidate wrong margin: -0.001068354

m314_continuity_surface:
  threshold: -0.000526897
  candidate wrong margin: -0.000785202

m317_continuity_surface:
  threshold: -0.000527269
  candidate wrong margin: -0.000785941
```

This directly addresses the M1120 failure: row15 wrong-history rollouts remain
unsafe with slack instead of crossing zero.

## First Replay

The selected alpha passes the same six-surface first replay used in M1120:

```text
m183_m168:            pass, 16/16 success drops retained
m223_m219:            pass, 17/17 success drops retained
m267_m264:            pass, 17/17 success drops retained
current_m333_surface: pass, 17/17 success drops retained
m314_continuity:      pass, 17/17 success drops retained
m317_continuity:      pass, 17/17 success drops retained
```

Aggregate deltas are small and positive:

```text
normal_success_delta:        0.0 on every surface
wrong_history_success_delta: 0.0 on every surface
normal_margin_mean_delta:    about 0.000236 on 5/6 surfaces
margin_gap_mean_delta:       about 0.000036 on 5/6 surfaces
```

## Artifacts

```text
runs/m1123_row15_unsafe_margin_projection_probe/summary.json
runs/m1123_row15_unsafe_margin_projection_probe/projection_candidates.csv
runs/m1123_row15_unsafe_margin_projection_probe/row15_gate_rows.csv
runs/m1123_row15_unsafe_margin_projection_probe/row15_replay_rows.csv
runs/m1123_row15_unsafe_margin_projection_probe/first_replay_summary.csv
runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

## Interpretation

M1123 validates the M1122 hypothesis: the M1118 direction was not useless, but
the full step was too large for row15's terminal-margin cliff. A no-training
projection with alpha `0.15` keeps exact M1107 improvement while preserving
row15 wrong-history unsafe terminal margins and the M1120 first replay stack.

This is still not promotable. It has not run family-intersection replay, full
public gate, fresh/OOD, behavior gates, private holdout, or PPO. The only valid
claim is that a nonzero trust-region projection exists for the M1118 direction.

## Decision

```text
row15_unsafe_margin_projection_first_replay_candidate_route_to_family_replay_design
```

Next milestone:

```text
m1124-v4-public-base-row15-projection-family-replay-design
```
