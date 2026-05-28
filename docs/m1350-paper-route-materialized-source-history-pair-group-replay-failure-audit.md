# M1350 Paper-Route Materialized Source-History Pair-Group Replay Failure Audit

## Summary

M1350 audits the M1349 replay failure of the M1346 objective-positive candidate.

Decision:

```text
materialized_source_history_replay_failure_audit_route_to_interpolation_preflight_design
```

This is audit-only. It does not train, run PPO, run more replay, use private
holdout, change actor inputs, or promote.

## What Failed

M1346 candidate:

```text
runs/m1346_materialized_source_history_pair_group_update/checkpoints/raw_pair_group_update.pt
```

M1349 first replay surface:

```text
M267/M264
```

Failure:

```text
gate_pass: false
rows: 17
baseline_normal_success_rate: 1.0
candidate_normal_success_rate: 0.0
normal_success_delta: -1.0
baseline_success_drop_count: 17
candidate_success_drop_count: 0
success_drop_count_delta: -17
normal_margin_mean_delta: -0.1065894892
margin_gap_mean_delta: -0.0132868003
```

Terminal reasons:

```text
M1154 normal: obstacle_completed 17 / 17
M1154 wrong-history: collision 17 / 17
M1346 normal: collision 17 / 17
M1346 wrong-history: collision 17 / 17
```

M183/M170 was correctly skipped because M267/M264 failed first.

## What This Means

M1349 is not a subtle metric artifact. The candidate destroys the normal branch
on the first current-family proof surface.

This is different from earlier failures where an update made the wrong-history
branch too safe. Here the M1346 update makes both normal and wrong-history
branches collide:

```text
normal branch: safe -> collision
wrong-history branch: collision -> collision
success-drop proof: retained 17 -> retained 0
```

The M1346 objective result is therefore insufficient as a replay admission
criterion.

## Root Cause Classification

Primary classification:

```text
proof_washout
```

Specific subtype:

```text
current_family_normal_branch_collision
```

Most likely control variable:

```text
update amplitude / trust region
```

Evidence:

```text
M1346 changed only the allowed scope, but allowed_parameter_l2 was 1.3300853209
and allowed_parameter_max_abs was 0.0315537974.
```

The objective update strongly improved fixed zero-context source-history
metrics:

```text
combined_loss_mean: 6.8847534022 -> 1.9998926339
group_min_joint_margin_mean: -6.8026667906 -> -1.1251848645
```

But closed-loop M267/M264 normal margin collapsed:

```text
normal_margin_mean_delta: -0.1065894892
```

This points to a trust-region gap between fixed source-current metrics and
closed-loop proof retention. It does not yet prove the pair-group objective is
useless; it proves the raw M1346 step is too large or missing replay-aware
normal-branch retention.

## Rejected Routes

Reject:

```text
continue full public replay
```

Reason:

```text
M267/M264 already failed every retention criterion.
```

Reject:

```text
run PPO from M1346
```

Reason:

```text
candidate normal branch already collides on the first proof surface.
```

Reject:

```text
promote M1346 or treat it as a new public base
```

Reason:

```text
proof replay fails before any behavior or generalization gate.
```

Reject for now:

```text
immediately redesign the source-history objective
```

Reason:

```text
we have not yet checked whether a smaller interpolation of the M1346 direction
preserves M267/M264 while retaining some exact objective improvement.
```

## Next Route

Next should be an interpolation/trust-region replay preflight design:

```text
m1351-paper-route-materialized-source-history-interpolation-preflight-design
```

The goal is to test whether the M1346 direction has a usable small-alpha region.

Candidate alphas should be conservative:

```text
0.005
0.01
0.02
0.05
0.10
0.20
```

Evaluation order:

```text
1. create interpolated checkpoints between M1154 base and M1346 raw;
2. verify actor input config and allowed mutation scope;
3. recompute exact M1339/M1342 materialized source-history metrics;
4. run M267/M264 replay for candidates that retain objective improvement;
5. run M183/M170 only for candidates passing M267/M264;
6. do not promote even if an interpolation passes.
```

Acceptance should be lexicographic:

```text
M267/M264 gate_pass is mandatory;
M183/M170 gate_pass is mandatory if M267/M264 passes;
exact source-history metrics should improve over M1154;
forbidden parameters and log_std must remain unchanged;
no PPO, private holdout, promotion, or actor-input change.
```

If no alpha passes M267/M264:

```text
route to replay-aware active-set repair design
```

If a small alpha passes replay but gives negligible objective improvement:

```text
classify M1346 direction as too weak under usable trust region and redesign the
objective with replay-aware normal-branch retention.
```

If a small alpha passes replay and preserves meaningful exact objective lift:

```text
route to limited two-surface repeat or full public replay design, not promotion.
```

## Decision

M1350 rejects raw M1346 as a replay candidate and routes to interpolation
preflight design. The scientific lesson is clear:

```text
fixed source-history objective improvement must be guarded by closed-loop replay
retention; otherwise it can destroy the normal branch while improving the
diagnostic objective.
```
