# M1353 Paper-Route Materialized Source-History Interpolation Replay Result Audit

## Summary

M1353 audits the M1352 interpolation preflight result.

Decision:

```text
materialized_source_history_interpolation_replay_audit_route_to_replay_aware_retention_design
```

M1352 found a nonzero replay-safe trust-region point:

```text
selected_alpha: 0.005
selected_checkpoint: runs/m1352_materialized_source_history_interpolation_preflight/checkpoints/alpha_0_005.pt
```

This is useful evidence, but it is not strong enough to justify promotion,
PPO, private holdout, or full-public-replay escalation as the next main step.
The selected alpha should be treated as a diagnostic proof that raw M1346
overshot a small replay-safe region.

## Evidence From M1352

All alphas were exact-admitted:

```text
exact_candidate_count: 6 / 6
actor_inputs_changed: false
forbidden_parameter_mutation_detected: false
log_std_l2: 0.0
```

The exact metrics improved monotonically with alpha:

| alpha | combined delta | group-min delta | eval-fold delta | M267/M264 | M183/M170 |
| ---: | ---: | ---: | ---: | --- | --- |
| 0.005 | -0.031707 | +0.032248 | +0.029937 | pass | pass |
| 0.010 | -0.063395 | +0.064496 | +0.059871 | pass | fail |
| 0.020 | -0.126712 | +0.128975 | +0.119736 | pass | fail |
| 0.050 | -0.316172 | +0.322358 | +0.299286 | fail | skipped |
| 0.100 | -0.630206 | +0.644513 | +0.598373 | fail | skipped |
| 0.200 | -1.250839 | +1.277121 | +1.185753 | fail | skipped |

The replay-safe region is therefore bounded by the older M183/M170 surface
around `alpha=0.005`, even though M267/M264 tolerates up to `alpha=0.02`.

## Supported Claims

Supported:

```text
The M1346 update direction is not completely invalid; a very small nonzero
interpolation preserves the first two public replay proof surfaces.
```

Supported:

```text
The raw M1346 replay failure is amplitude-sensitive and should be treated as a
trust-region / retention problem, not as a forbidden mutation or actor-contract
artifact.
```

Supported:

```text
The limiting surface is currently M183/M170, not M267/M264.
```

## Falsified Or Unsupported Claims

Unsupported:

```text
Pure interpolation has recovered a meaningful new driver checkpoint.
```

Reason: the only passing alpha is `0.005`; its allowed-parameter L2 is only
`0.0066504331`, and its exact lift is weak.

Unsupported:

```text
The selected alpha materially improves the source-history directionality
problem.
```

Reason: at the selected alpha:

```text
group_all_rows_both_directional_count: 0
group_both_negative_count: 4
```

The update improves continuous exact metrics but does not convert any source
groups into all-rows-both-directional groups.

Unsupported:

```text
The selected alpha is a promotion candidate.
```

Reason: it has only passed two preflight replay surfaces, not the full public
gate stack, not fresh/generalization gates, and not behavior retention.

## Route Decision

Do not route directly to PPO.

Do not promote `alpha=0.005`.

Do not spend the next milestone on full-public-replay escalation. Full replay
may be useful later, but the current alpha is too small and too diagnostic to
be the highest-leverage next step.

Route instead to:

```text
m1354-paper-route-materialized-source-history-replay-aware-retention-design
```

The next design should make replay retention a first-class part of the update
problem rather than relying on post-hoc interpolation. In solver terms, M1346
optimized the source-history objective while ignoring active closed-loop replay
constraints. M1352 found the line-search boundary. M1354 should design the
active-set constrained update.

## M1354 Design Requirements

M1354 should keep the public-gate base as M1154:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

The M1352 `alpha=0.005` checkpoint is a diagnostic artifact, not the new base.

The replay-aware retention design should include:

```text
exact source-history objective:
  M1336/M1339/M1342 materialized row and pair-group metrics

replay active set:
  M267/M264 rows from the preflight
  M183/M170 rows from the preflight
  especially rows that fail between alpha 0.005 and alpha 0.02

retention target:
  preserve normal-history success
  preserve success-drop count
  bound normal margin regression
  bound margin-gap regression
```

The first implementation after design should remain no-PPO and public-only.
It may use action anchors, terminal-margin retention, or lexicographic exact
repair terms, but it must not relax thresholds or add actor inputs.

## Guardrails

M1353 performs no training, PPO, actor update, replay run, private holdout,
promotion, threshold relaxation, actor-input expansion, high-fidelity claim,
paper-level claim, or closed-loop self-identification claim.

## Next

```text
m1354-paper-route-materialized-source-history-replay-aware-retention-design
```
