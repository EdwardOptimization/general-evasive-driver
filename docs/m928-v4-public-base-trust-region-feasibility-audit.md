# M928 V4 Public-Base Trust-Region Feasibility Audit

## Purpose

M928 audits the M927 feasibility result and decides the next branch route.

M928 is process-only:

```text
no training
no residual fitting
no M880 exact compatibility
no replay
no PPO
no checkpoint promotion
```

## Audit Finding

M927 is a clean no-training feasibility result:

```text
sample_reconstruction_success_rate: 1.0
joined_target_rows: 122 / 122
grid_rows: 121
feasible_candidate_count: 0
tail_lift_rows: 22
normal_retained_tail_lift_rows: 0
training_started: false
actor_backbone_changed: false
```

This means:

```text
existing residual directions can move low-tail metrics;
existing residual directions can retain normal actions;
but not at the same alpha/mix point.
```

## Failure Classification

Classification:

```text
promotion_gate_failure
```

Reason:

```text
The feasibility grid contains no row that can be admitted toward exact
compatibility. Tail lift requires action drift outside the normal-retention
gate.
```

This is not:

```text
contract_violation
lineage_invalid
training_instability
scenario_sampling_failure
metric_artifact
```

## Implication

The public-base residual-head bridge has reached a local stop condition.

Continuing to train another residual objective would be a narrow gate-passing
loop unless it first changes the control variable. The evidence now says:

```text
global residual direction + scalar alpha is the wrong control surface for this
public-base low-tail problem.
```

The next highest-leverage route is a policy-level trust-region design, not
another residual-head loss variant.

## Next Route

Open:

```text
v4_public_base_policy_level_trust_region
```

Next:

```text
m929-v4-public-base-policy-level-trust-region-design
```

The design should ask:

```text
Can a tightly guarded actor-level update, with exact proof gates before replay
or PPO, change the policy in a way the frozen residual bridge cannot?
```

The design must keep the P0 actor input contract unchanged and must not run PPO
before objective sanity and proof-retention gates are pre-registered.

## Safeguards

M929 must preserve:

```text
M399 public-gate base as parent checkpoint;
P0 human-view no-wheel actor contract;
strict actor checksum tracking before and after update;
objective sanity before replay;
proof replay before PPO;
no promotion without proof, behavior, and generalization gates.
```

M929 must not:

```text
weaken normal-retention gates to accept M927;
run exact compatibility directly from a no-candidate residual direction;
start PPO;
promote a checkpoint.
```

## Decision

Decision:

```text
public_base_trust_region_feasibility_audit_route_to_policy_level_trust_region_design
```

Next:

```text
m929-v4-public-base-policy-level-trust-region-design
```
