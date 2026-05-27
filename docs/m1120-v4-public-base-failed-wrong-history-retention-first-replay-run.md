# M1120 V4 Public Base Failed Wrong-History Retention First Replay Run

## Purpose

M1120 runs the target-base first replay gate designed in M1119 for the M1118
best candidate.

This milestone runs only old-public and source-diverse first replay. It does
not train actor weights, run PPO, run family-intersection replay, run full
public replay, run fresh/OOD, run behavior gates, promote a checkpoint, use
private holdout, or change actor inputs.

## Candidate

```text
base policy: m399_base
base checkpoint:
  runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt

candidate policy: m1118_seed111800
candidate checkpoint:
  runs/m1118_failed_wrong_history_retention_actor_update_seed111800/optimized_checkpoint.pt
```

## Result

M1120 fails target-base first replay:

```text
result_class: failed_wrong_history_retention_first_replay_failed_wrong_history_safe
surface_count: 6
passed_surface_count: 2
failed_surface_count: 4
old_public_first_replay_pass: false
source_diverse_first_replay_pass: false
target_base_first_replay_pass: false
lost_success_drop_events: 4
normal_lost_events: 0
wrong_history_safe_events: 4
```

Passed surfaces:

```text
m183_m168:
  baseline success drops: 16
  candidate success drops: 16

m223_m219:
  baseline success drops: 17
  candidate success drops: 17
```

Failed surfaces:

```text
m267_m264:
  baseline success drops: 17
  candidate success drops: 16
  failure_class: wrong_history_safe

current_m333_surface:
  baseline success drops: 17
  candidate success drops: 16
  failure_class: wrong_history_safe

m314_continuity_surface:
  baseline success drops: 17
  candidate success drops: 16
  failure_class: wrong_history_safe

m317_continuity_surface:
  baseline success drops: 17
  candidate success drops: 16
  failure_class: wrong_history_safe
```

All four lost rows are the same physical pair and row id:

```text
row_id: 15
target: future_braking_deceleration
physical_pair_key: 9530:21:9550:21
left_step/right_step: 21/21
normal_lost: false
wrong_history_safe: true
```

The candidate improves normal margins on aggregate, but one wrong-history branch
crosses from negative to positive margin on row 15. Therefore the first replay
failure is still the M1112-style proof-washout failure, only much narrower.

## Artifacts

```text
runs/m1120_failed_wrong_history_retention_first_replay/summary.json
runs/m1120_failed_wrong_history_retention_first_replay/first_replay_summary.csv
runs/m1120_failed_wrong_history_retention_first_replay/lost_success_drop_rows.csv
```

Per-surface run directories:

```text
runs/m1120_failed_wrong_history_retention_first_replay/m183_m168
runs/m1120_failed_wrong_history_retention_first_replay/m223_m219
runs/m1120_failed_wrong_history_retention_first_replay/m267_m264
runs/m1120_failed_wrong_history_retention_first_replay/current_m333_surface
runs/m1120_failed_wrong_history_retention_first_replay/m314_continuity_surface
runs/m1120_failed_wrong_history_retention_first_replay/m317_continuity_surface
```

## Interpretation

M1118's retention-aware update improved the situation relative to M1112 but did
not solve it. M1112 lost `47` success-drop events; M1120 loses `4`, all on the
same row-15 physical pair. That is progress, but not a pass.

The next step should be an audit, not another update or replay escalation. The
audit should answer:

```text
1. Was row 15 included in the M1115 target-base trajectory anchor?
2. Did target-base trajectory-anchor MSE stay small while the terminal margin
   crossed zero?
3. Is row 15 a terminal-margin cliff requiring row-specific margin retention?
4. Did action drift concentrate at late trajectory steps rather than first
   action?
5. Should the next repair add row15 terminal-margin retention, a radius hinge,
   or a wrong-history unsafe-margin objective?
```

## Decision

```text
failed_wrong_history_retention_first_replay_reject_wrong_history_safe_route_to_audit
```

Next milestone:

```text
m1121-v4-public-base-failed-wrong-history-retention-first-replay-failure-audit
```
