# M1231 Paper-Route Short-Horizon Partial Positive Audit

## Summary

M1231 audits the partial positive M1230 short-horizon relocation result.

Decision:

```text
short_horizon_partial_positive_pivot_to_extreme_fault_source_generation
```

M1230 is useful because it shows the materialization mechanism can create
wrong-history success drops:

```text
accepted_wrong_rows: 80
success_drop_fraction: 1.0
normal_success: true
variant_success: false
```

But it is not proof-quality:

```text
accepted_wrong_left_steps: 2
accepted_wrong_targets: 1
accepted_wrong_checkpoints: 1
accepted_wrong_normal_margin_buckets: 1
accepted_wrong_margin_gap_mean: 0.0022355233
```

No training, PPO, promotion, private holdout, profile tuning, actor-input
change, or self-identification claim occurs in M1231.

## What M1230 Supports

Supported narrow claim:

```text
The current tooling can materialize M1226 action-divergent wrong-history rows
into short-horizon success drops under obstacle relocation.
```

Important details:

```text
accepted rows are true success drops
normal branch survives the 12-step horizon
wrong-history branch collides
the source candidate gate was ready before replay
```

This is a real mechanism signal, not just an action-distance artifact.

## What M1230 Does Not Support

Blocked claims:

```text
source-diverse causal-history proof
long-horizon evasive-driver performance
history necessity across scenario distribution
recurrent belief or online self-identification
training readiness
paper-level result
promotion
```

The accepted surface is too narrow:

```text
target: unavoidable only
left steps: 18 and 21 only
checkpoint: l3_s111602 only
normal margin bucket: one bucket
mean margin gap: 0.0022355233
```

The signal is therefore a local active set, not a robust proof surface.

## Rejected Next Steps

Do not:

- train from the 80 accepted rows;
- lower source-diversity thresholds;
- call M1230 a proof pass;
- report short-horizon rows as long-horizon evasive-driving performance;
- keep tuning the same M1226 public source pool until it passes.

The last point matters. M1225-M1230 already showed that the current natural
M1222 source pool can produce a local signal, but not a source-diverse surface.
More local grid tuning is likely to overfit this public pool.

## Selected Next Route

Pivot the branch from:

```text
paper_route_terminal_boundary_materialization
```

to:

```text
paper_route_extreme_fault_source_generation
```

Rationale:

```text
The project needs source-diverse situations where hidden dynamics differences
matter, not more tuning around one short-horizon unavoidable active set.
```

The new source branch should explicitly cover high-stress and fault-like
conditions that a general evasive driver should handle:

```text
sudden friction drop
split-mu road
localized tire grip loss
front/rear axle grip asymmetry
brake fade or brake scale loss
steering actuator lag or partial steering loss
drive torque loss / half-shaft failure proxy
tire blowout proxy
mass / CG / inertia shift
sensor delay or IMU noise
obstacle timing at AEB-infeasible distances
```

These are hidden simulator conditions and must not enter actor observation.
They can be used for scenario generation, logging, teacher/oracle diagnostics,
and corpus mining.

## M1232 Scope

M1232 should design the extreme/fault source-generation branch:

```text
1. define scenario families and hidden parameter ranges;
2. define no-oracle actor-input guardrails;
3. define source-mining outputs compatible with existing matched-history and
   relocation tooling;
4. define source-diversity gates;
5. define how to avoid turning fault labels into actor inputs;
6. choose the first bounded implementation step.
```

M1232 should not train or run PPO.

## Decision

```text
short_horizon_partial_positive_pivot_to_extreme_fault_source_generation
```

The terminal-boundary materialization branch has produced useful evidence but
should not continue as a narrow public-pool grid-tuning loop.
