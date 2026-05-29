# M1510 Paper-Route Decisive History Bounded Runner Design

## Summary

M1510 designs the bounded fixed-policy runner needed after the M1509 synthesis.

Decision:

```text
decisive_history_bounded_runner_design_admit_implementation
```

This milestone is design only. It does not run rollout collection, replay, PPO,
training, promotion, private holdout, corpus export, actor-input changes,
candidate materialization, or level3 self-ID claims.

## Purpose

M1499-M1508 built the decisive-history task matrix, hook specs, reset-only
runtime smoke, and candidate materialization guards. That branch proved
infrastructure, not real source traces.

The next evidence gap is:

```text
Can the current simulator plus fixed public policy produce bounded, measurable
source traces for all six T4/T5 source families without training or shortcuts?
```

The runner must answer only that plumbing question. It must not decide whether
a row is a true decisive-history candidate; M1508 materialization remains a
later step after measured distances and intervention margins exist.

## Fixed Scope

Runner scope for the first implementation:

```text
checkpoint:
  runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt

policy:
  deterministic checkpoint actor
  P0 human-view no-wheel frame
  online recurrent hidden state persists through episode

hook specs:
  default_hook_specs(seed_count=1)
  at most one spec per source family
  expected max spec count: 6

rollout budget:
  max_rollout_steps: 96
  stop on terminated or truncated
  no continuation interventions
  no replay gate

device:
  cpu by default

run_dir:
  runs/m1511_decisive_history_bounded_runner_smoke
```

The budget intentionally covers the largest current M1506 decision step:

```text
max decision_step: 48
max_rollout_steps: 96
```

This leaves room for post-decision behavior while keeping the smoke small.

## Separation From Candidate Materialization

M1511 should produce source traces only:

```text
source trace rows -> source snapshots -> source-family summaries
```

It must not call candidate materialization as part of the runner smoke:

```text
candidate_materialized: false
training_corpus_exported: false
```

The later measured-candidate milestone may consume source traces and run the
M1508 materialization guard, but that should be a separate manifest so the
project can audit trace quality before accepting candidates.

## Runner Pipeline

The implementation should add a small no-training module, for example:

```text
src/autodrift/decisive_history_bounded_runner.py
tests/test_decisive_history_bounded_runner.py
```

Pipeline:

```text
1. load fixed checkpoint with load_actor_critic_checkpoint
2. assert P0-compatible human-view no-wheel actor contract
3. build bounded hook specs from default_hook_specs(seed_count=1)
4. instantiate AutoDriftEnv for each spec
5. reset env with spec.seed
6. run deterministic ActorPolicy for max_rollout_steps or until done
7. record per-step source trace rows
8. record snapshot rows at reveal, decision, post-decision, and terminal steps
9. write source-family summary and guardrail summary
10. write summary.json
```

The runner may use privileged simulator `info` fields for metadata and
diagnostics. Those fields must not enter actor observations.

## Trace Schema

`source_trace_rows.csv` should contain one row per environment step:

```text
trace_id
source_family
task_family
candidate_id
seed
capability_pair
geometry_key
reveal_step
decision_step
step
phase
terminated
truncated
reward
action_steer
action_throttle
action_brake
hidden_norm
hidden_checksum
observation_dim
info_obstacle_label
info_obstacle_distance
info_obstacle_lateral_offset
info_active_obstacle_body_x
info_active_obstacle_body_y
info_min_clearance_margin
info_collision
info_obstacle_completed
info_warmup_gate_visible
info_warmup_gate_clearance_margin
info_friction_step_at
info_friction_step_applied
info_mu
info_initial_mu
info_brake_scale
info_drive_scale
info_steer_tau_scale
```

The `info_*` fields are metadata only. They are allowed for mining and audits,
but they are forbidden actor inputs.

`phase` should be deterministic:

```text
pre_reveal
reveal
between_reveal_and_decision
decision
post_decision
terminal
```

## Snapshot Schema

`source_snapshot_rows.csv` should include a compact subset:

```text
trace_id
source_family
task_family
candidate_id
seed
snapshot_kind
step
phase
action_steer
action_throttle
action_brake
hidden_norm
min_clearance_margin
collision
obstacle_completed
terminal_reason
```

Required snapshot kinds:

```text
reveal_step
decision_step
decision_plus_8
decision_plus_16
terminal
```

Missing snapshot kinds are allowed only if the episode terminates before the
target step; the row should then be represented by a source-family failure
reason rather than silently dropped.

## Summary Schema

`summary.json` should contain:

```text
result_class: decisive_history_bounded_runner_smoke
checkpoint
spec_count
source_family_count
max_rollout_steps
trace_row_count
snapshot_row_count
rollout_success_count
rollout_failure_count
failure_type_counts
source_families_completed
source_families_reached_reveal
source_families_reached_decision
source_families_reached_post_decision
guardrail_violation_count
candidate_materialized: false
training_started: false
evaluation_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

The summary should distinguish runner completion from evidence usefulness.
Reaching the decision step is useful; failing before the decision step should be
classified and saved, not hidden.

## Failure Taxonomy

Expected runner failure labels:

```text
none
scenario_sampling_failure
checkpoint_load_failure
contract_violation
reset_failure
rollout_exception
did_not_reach_reveal_step
did_not_reach_decision_step
nonfinite_observation
nonfinite_action
```

If a new failure class is needed, add it deliberately instead of flattening it
into `training_instability`.

## Guardrails

M1511 must keep these false:

```text
candidate_materialized
training_started
evaluation_started
replay_started
ppo_used
promoted
private_holdout_used
actor_input_contract_changed
training_corpus_exported
labels_enter_actor_input
level3_self_id_claim_made
```

No labels, hidden physical parameters, success flags, collision flags,
terminal margins, TTC, oracle feasibility, or path-reference features may be
added to actor observations.

## Acceptance Criteria For M1511

M1511 should pass if:

```text
focused tests for the runner pass;
the bounded runner smoke writes all required artifacts;
checkpoint loading and actor-contract assertions pass;
all six source families are attempted;
failure rows are explicit for any incomplete source;
guardrail_violation_count == 0;
candidate_materialized == false;
training/replay/PPO/promotion/private holdout remain false.
```

M1511 should not require all six families to produce useful candidates. It
should require truthful trace and failure artifacts. Candidate usefulness is the
next audit step.

## Next Milestone

Next:

```text
m1511-paper-route-decisive-history-bounded-runner-implementation
```

M1511 implements the fixed-policy trace runner and runs the bounded public
smoke. The follow-up after M1511 should audit whether the produced traces are
eligible for measured T4/T5 materialization, not start training.
