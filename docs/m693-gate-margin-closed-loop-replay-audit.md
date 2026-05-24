# M693 Gate-Margin Closed-Loop Replay Audit

## Purpose

M693 is a process synthesis milestone for the
`response_amplification_actor_coupling` branch.

It answers:

```text
After M692 replay_neutral, should the response-amplification residual-head
branch continue, stop, or pivot before any actor update or PPO?
```

This milestone is audit-only:

```text
no training
no residual-head update
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

The branch began after repeated wrong-history source-mining failures showed that
existing surfaces were not action/outcome critical enough:

```text
M661: 0 accepted action-divergent rows
M664: action gaps existed, but action-threshold rows were already normal-failed
M667: 204 near-boundary preferred windows, but no sustained wrong-history outcome gap
M668: admitted response-amplification because the available surfaces were not yet closed-loop action critical
```

M669-M672 established a useful frozen diagnostic signal:

```text
M671: reconstructed 648-row source-balanced shadow corpus
M671: fused-plus-next-hidden shadow heads passed in 2 / 3 seeds
M672: classified this as representation/action-boundary evidence, not closed-loop proof
```

M673-M688 then tried to couple that signal to a conservative residual head while
preserving normal behavior:

```text
M674: exact gate failed due to first-action drift versus sequence-gap conflict
M677: first-step safety improved, but wrong-history sequence gap collapsed
M680: wrong-history gap partially restored, but normal full-sequence retention failed
M683: normal retention improved, but wrong-history gap was suppressed
M686: normal retention strong, but gates collapsed and wrong gap stayed too small
M689: gate-margin objective passed exact output gates in 3 / 3 seeds
```

M690 recorded the key caveat:

```text
M689 is a real exact output-level pass, but not a clean gate-factorized
self-identification result and not a closed-loop behavior pass.
```

M691 designed the closed-loop replay admission gate, and M692 implemented it.

M692 result:

```text
rows_attempted:                 120
rows_reconstructable:           120
rows_replayed:                  360
actor_parameters_changed:       false
base_actor_checkpoint_written:  false
training_started:               false
ppo_used:                       false
promoted:                       false
normal_first_action_l2_p95:      0.003928
normal_margin_regression_p95:    0.000008
wrong_risk_improvement_mean:     0.000025
wrong_success_improvement_count: 0
wrong_collision_reduction_count: 0
replay_result_class:             replay_neutral
replay_admission_passed:         false
```

So the implementation is clean, but the scientific admission fails: output-level
residual separation did not produce meaningful short-horizon trajectory utility.

## Supported Claims

The branch supports these claims:

```text
1. The current frozen actor contains some response-sensitive representation
   signal that can be exposed by diagnostic heads.

2. Exact output-level residual objectives can be made to preserve normal
   first-action behavior while amplifying wrong-history output separation.

3. The no-training replay harness can reconstruct source-heldout snapshots and
   test first-action residual corrections without mutating the actor.

4. The harness correctly prevented a diagnostic exact pass from being promoted
   into actor update, PPO, or driver claims.
```

## Falsified Claims

The branch falsifies or fails to support these stronger claims:

```text
1. M689 residual heads are trajectory-useful enough to admit actor coupling.

2. Exact output separation is sufficient evidence for closed-loop
   self-identification.

3. More scalar residual-head loss tuning is the right next lever.

4. The current M671/M689 source-heldout surface is a strong action-critical
   closed-loop surface.
```

The important distinction is:

```text
M689 exact output pass: true
M692 closed-loop replay utility: not shown
```

## Failure Taxonomy Summary

Primary failure label:

```text
metric_artifact
```

Reason:

```text
The exact output metrics improved and eventually passed, but their improvement
did not translate into the replay gate's closed-loop risk, success, or collision
metrics.
```

Secondary labels:

```text
objective_overfit risk:
  The residual objectives became good at satisfying the public source-heldout
  exact metrics without becoming trajectory-useful.

scenario_sampling_failure risk:
  The available response-amplification rows may not contain enough true
  terminal-margin-sensitive action-critical cases.
```

This is not classified as:

```text
proof_washout:
  The actor was unchanged and no old proof rows were washed out.

training_instability:
  No actor training or PPO occurred in M692.

contract_violation:
  The P0 human-view actor input contract was unchanged.
```

## Public Gate Overfit Risk

The risk is now high enough to force a branch pivot.

M669-M692 repeatedly optimized the same family of public response-amplification
diagnostics:

```text
shadow sequence gap
normal first-action retention
normal sequence retention
wrong-history sequence gap
gate activation margin
exact source-heldout alpha ladder
```

That was useful for diagnosis, but M692 shows the branch can pass or nearly pass
those output metrics while not moving the closed-loop trajectory metrics that
matter.

Future work should not add another narrow residual objective on the same public
surface unless a new replay-positive or trajectory-sensitive surface is first
constructed.

## Next Branch Decision

Synthesis decision:

```text
pivot
```

Closed branch:

```text
response_amplification_actor_coupling
```

New branch:

```text
trajectory_terminal_boundary_source_mining
```

Reason:

```text
The next bottleneck is not residual-head capacity. The bottleneck is the lack of
a source surface where small control changes have measurable terminal-margin or
collision consequences under normal versus wrong/counterfactual history.
```

The next branch should first mine or construct rows with actual closed-loop
trajectory sensitivity:

```text
normal-history rollout is successful or near-boundary
wrong/counterfactual-history rollout is worse, or a controlled action
perturbation creates a measurable margin/risk delta
the row is not already normal-failed
terminal margin has enough slack structure to distinguish useful corrections
source diversity is enforced before objective design
```

Only after that source exists should the project design another actor-coupling,
repair, PPO, or sequence-head objective.

## Decision

Do not:

```text
continue response-amplification residual-head tuning on the M671/M689 public
surface
run actor update from M689 residual heads
run PPO from M689 residual heads
promote any checkpoint
weaken the closed-loop replay admission standard
```

Do:

```text
start M694 as trajectory/terminal-boundary source-mining design
make terminal-margin sensitivity and closed-loop replay utility first-class
mine before optimizing
keep actor input contract unchanged
keep M689/M692 artifacts as diagnostics, not deployment candidates
```

## Synthesis Artifact Checklist

Required synthesis questions:

```text
evidence_summary: recorded above
supported_claims: recorded above
falsified_claims: recorded above
failure_taxonomy_summary: recorded above
public_gate_overfit_risk: recorded above
next_branch_decision: pivot to trajectory_terminal_boundary_source_mining
```

## Decision String

```text
gate_margin_replay_audit_pivot_to_trajectory_boundary_mining
```

## Next

```text
m694-trajectory-terminal-boundary-source-mining-design
```
