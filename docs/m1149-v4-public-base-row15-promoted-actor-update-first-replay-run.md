# M1149 V4 Public Base Row15 Promoted Actor Update First Replay Run

## Purpose

M1149 runs the first closed-loop replay gate designed in M1148 for the M1147
best candidate:

```text
baseline policy: row15_current
baseline checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt

candidate policy: m1147_114602
candidate checkpoint:
  runs/m1147_row15_promoted_actor_coupling_anchor100_s10_lr5e5_seed114602/optimized_checkpoint.pt
```

This milestone runs only first replay over old-public, source-diverse, and
row15-promoted materialized proof surfaces. It does not train actor weights,
run PPO, run M1061 family-intersection replay, run fresh/OOD or behavior
gates, promote a checkpoint, use private holdout, or change actor inputs.

## Result

M1149 rejects `m1147_114602` at first replay:

```text
result_class: row15_promoted_first_replay_rejected_wrong_history_safe
surface_count: 10
passed_surface_count: 8
failed_surface_count: 2
old_public_first_replay_pass: false
source_diverse_first_replay_pass: true
row15_promoted_materialized_replay_pass: false
first_replay_pass: false
lost_success_drop_events: 76
normal_lost_events: 0
wrong_history_safe_events: 76
failure_class: wrong_history_safe
```

Eight surfaces pass:

```text
m183_m168:              16 / 16 success drops retained
m183_m170:              17 / 17 success drops retained
m193_m189:              14 / 14 success drops retained
m212_m204:              17 / 17 success drops retained
m223_m219:              17 / 17 success drops retained
current_m333_surface:   17 / 17 success drops retained
m314_continuity_surface:17 / 17 success drops retained
m317_continuity_surface:17 / 17 success drops retained
```

Two surfaces fail:

```text
m267_m264:
  baseline success drops: 17
  candidate success drops: 16
  lost success-drop events: 1
  failure_class: wrong_history_safe

row15_promoted_materialized:
  baseline success drops: 148
  candidate success drops: 73
  lost success-drop events: 75
  failure_class: wrong_history_safe
```

The failure is not normal-history collapse. The candidate keeps normal success
rate at `1.0` on every surface. The failure is that wrong-history rollouts
become safe:

```text
normal_lost_events: 0
wrong_history_safe_events: 76
```

The old-public failure is the familiar row-15 event:

```text
surface: m267_m264
row_id: 15
target: future_braking_deceleration
physical_pair_key: 9530:21:9550:21
baseline wrong-history margin: -0.000294
candidate wrong-history margin:  0.000391
```

The row15-promoted materialized failures are concentrated in
`future_braking_deceleration` rows from the promoted-base materialized surface.
The largest failing groups are:

```text
113201:21:113230:48  left/right steps 21/48  lost rows: 12
113201:18:113230:45  left/right steps 18/45  lost rows: 12
113201:24:113230:51  left/right steps 24/51  lost rows: 12
113201:15:113230:42  left/right steps 15/42  lost rows: 10
113201:24:113230:48  left/right steps 24/48  lost rows: 10
```

## Artifacts

```text
runs/m1149_row15_promoted_actor_update_first_replay/summary.json
runs/m1149_row15_promoted_actor_update_first_replay/first_replay_summary.csv
runs/m1149_row15_promoted_actor_update_first_replay/lost_success_drop_rows.csv
runs/m1149_row15_promoted_actor_update_first_replay/row15_promoted_materialized_corpus.csv
```

Per-surface replay directories:

```text
runs/m1149_row15_promoted_actor_update_first_replay/m183_m168
runs/m1149_row15_promoted_actor_update_first_replay/m183_m170
runs/m1149_row15_promoted_actor_update_first_replay/m193_m189
runs/m1149_row15_promoted_actor_update_first_replay/m212_m204
runs/m1149_row15_promoted_actor_update_first_replay/m223_m219
runs/m1149_row15_promoted_actor_update_first_replay/m267_m264
runs/m1149_row15_promoted_actor_update_first_replay/current_m333_surface
runs/m1149_row15_promoted_actor_update_first_replay/m314_continuity_surface
runs/m1149_row15_promoted_actor_update_first_replay/m317_continuity_surface
runs/m1149_row15_promoted_actor_update_first_replay/row15_promoted_materialized
```

`row15_promoted_materialized_corpus.csv` is a replay-compatible copy of the
M1142 materialized rows with an added `row_id` column. It does not change row
content or actor inputs.

## Interpretation

M1147's actor-coupling update improves the M1144 exact objective, but first
replay shows that the improvement does not preserve the promoted-base
materialized wrong-history surface. This is a proof-washout failure: the
normal branch remains successful, while wrong-history branches become safe.

This result is stronger than a single stale-row failure. The old public
`m267_m264` row-15 event still fails, and the new row15-promoted materialized
surface loses `75` additional success drops. The next step must be a
failure audit over M1144/M1147/M1149 artifacts before any new actor update,
family replay, behavior gate, PPO, or promotion.

## Decision

```text
row15_promoted_first_replay_reject_wrong_history_safe_route_to_failure_audit
```

Next milestone:

```text
m1150-v4-public-base-row15-promoted-first-replay-failure-audit
```
