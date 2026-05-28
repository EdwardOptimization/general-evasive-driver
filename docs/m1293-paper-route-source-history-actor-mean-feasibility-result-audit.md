# M1293 Paper-Route Source-History Actor-Mean Feasibility Result Audit

## Summary

M1293 audits the M1292 actor-mean directional feasibility probe.

Decision:

```text
source_history_actor_mean_feasibility_audit_mixed_route_to_pair_group_objective_design
```

M1292 is a mixed result:

```text
best_both_directional_fraction: 0.1842105263
best_both_positive_count: 28
best_mutually_exclusive_fraction: 0.7763157895
any_non_actor_mean_mutation_detected: false
```

This is enough to reject the strongest capacity-limited interpretation, but not
enough for PPO, promotion, or public replay gates.

## Evidence

M1292 tried two actor_mean-only initializations:

```text
base_init
m1288_init
```

Base initialization:

```text
both_directional_fraction: 0.1578947368
both_positive_count: 24
mutually_exclusive_fraction: 0.7631578947
min_margin_mean: -0.3929710263
```

M1288 initialization:

```text
both_directional_fraction: 0.1842105263
both_positive_count: 28
mutually_exclusive_fraction: 0.7763157895
min_margin_mean: -0.3045456347
```

Guardrail:

```text
any_non_actor_mean_mutation_detected: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
```

## Interpretation

Supported:

```text
Fixed source-history features plus actor_mean contain some directional signal:
both-positive rows increase from 0 to 28.
```

Not supported:

```text
Actor_mean-only is sufficient. The best candidate leaves 118/152 rows mutually
exclusive and has min_margin_p10=-1.8071264267.
```

Not supported:

```text
PPO readiness. The source-history relation is still weak and has not passed any
closed-loop retention stack.
```

## Next Step Decision

Choose:

```text
m1294-paper-route-source-history-pair-group-objective-design
```

Rationale:

```text
M1290 showed each pair/probe group has two rows. M1292 showed actor_mean can
turn some rows both-positive, but scalar row-wise optimization still leaves
most rows mutually exclusive. The next design should explicitly optimize
pair-group structure and penalize leaving one row correct at the expense of its
paired row.
```

M1294 should design:

```text
pair-group min-margin objective;
group-balance penalty;
hard report of both-positive rows per pair/probe group;
bounded actor_mean-only implementation first;
scope escalation only if actor_mean pair-group probe remains mixed/negative.
```

## Guardrails

Do not:

```text
promote M1292 candidate checkpoints;
start PPO;
use private holdout;
change actor inputs;
claim closed-loop driver improvement;
claim paper-level evidence;
claim level3 self-identification.
```

## Claim Discipline

M1293 supports:

```text
M1292 is mixed actor_mean directional feasibility evidence and should route to
pair-group objective design.
```

M1293 does not support:

```text
actor_mean-only solved;
PPO readiness;
promotion;
closed-loop self-identification;
paper-level generalization.
```

PPO and promotion remain blocked.
