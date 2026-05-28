# M1253 Paper-Route Capability-Separable Trajectory Proposal Source-Variable Audit

## Summary

M1253 audits the trajectory proposal source branch after M1252's targeted
margin-restoration smoke.

Decision:

```text
trajectory_proposal_source_near_miss_stop_same_budget_pivot_to_event_timing_source_design
```

The trajectory proposal source is useful but not sufficient under the current
source state/timing:

```text
accepted_separable_pairs: 0
```

The next variable should be source-state/event timing, not another proposal
budget or seed expansion.

## Evidence

M1250:

```text
trajectory_proposals: 425
accepted_separable_pairs: 0
pair 5 min two-sided cross-regret: 0.0239608733
pair 5 pair_min_best_margin: -0.0018868557
```

M1252:

```text
trajectory_proposals: 552
accepted_separable_pairs: 0
pair 5 min two-sided cross-regret: 0.0226062003
pair 5 pair_min_best_margin: -0.0006610772
```

The near-miss improved, but remained nonviable. This is not a reason to lower
thresholds, because the whole source claim depends on both hidden branches
having viable own-condition maneuvers.

## Failure Classification

Primary failure type:

```text
scenario_sampling_failure
```

Subtype:

```text
source_state_timing_near_miss
```

The current sampled emergency state is close to capability-separable, but the
own-condition best trajectories remain just below the viability threshold.
More action proposals moved the row closer, but not across zero.

Not classified as:

```text
contract_violation
training_instability
proof_washout
private_holdout_contamination
promotion_gate_failure
```

## Stop Decision

Stop expanding:

```text
same source states
same trajectory proposal source variable
more proposal seeds
more proposal count
more local relocation budget
```

Reason:

```text
M1251 allowed one targeted repair. M1252 used it and still produced zero
accepted rows. Another same-variable budget expansion would be local gate
chasing.
```

## Next Variable

Open event-timing/source-state design:

```text
m1254-paper-route-capability-separable-event-timing-source-design
```

The next source miner should test whether accepted capability-separable rows
exist when the emergency onset/snapshot timing changes, while keeping:

```text
same actor checkpoint
same no-training policy
same acceptance thresholds
same actor input contract
```

Examples of allowed source-state variables:

```text
snapshot step offset around near-miss seeds
obstacle longitudinal timing/onset offset
shorter or longer emergency continuation horizon as a source diagnostic
positive near-zero own-branch viability target
```

Forbidden:

```text
lowering min_cross_regret_margin
accepting negative own-branch margins
feeding timing/proposal labels into actor input
training or PPO
private holdout
promotion
```

## Claim Boundary

This audit supports:

```text
trajectory proposal source is stronger than fixed lattice;
the current source-state/timing still blocks accepted source rows;
the next evidence variable should be event timing/source state.
```

It does not support:

```text
self-identification
history necessity
PPO readiness
paper-level result
real-vehicle claim
overall project infeasibility
```
