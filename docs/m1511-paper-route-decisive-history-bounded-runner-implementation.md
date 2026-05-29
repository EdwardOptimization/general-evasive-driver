# M1511 Paper-Route Decisive History Bounded Runner Implementation

## Summary

M1511 implements the bounded fixed-policy source trace runner designed in
M1510 and runs the first public smoke.

Decision:

```text
decisive_history_bounded_runner_smoke_pass_route_to_trace_audit
```

This milestone does not materialize candidates, export a training corpus, run
replay, run PPO, train, promote, use private holdout, change actor inputs, or
claim level3 self-identification.

## Implementation

New code:

```text
src/autodrift/decisive_history_bounded_runner.py
tests/test_decisive_history_bounded_runner.py
```

The runner loads the fixed public checkpoint:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

It asserts the P0 actor contract:

```text
72-value human-view online recurrent actor;
history_length = 1;
action_history_mode = full;
include_privileged_params = false;
wheel_observation_mode = none;
obstacle_relative_velocity_mode = zero.
```

Privileged simulator `info` fields are written only as metadata.

## Smoke Command

```bash
PYTHONPATH=src python -m autodrift.decisive_history_bounded_runner \
  --run-dir runs/m1511_decisive_history_bounded_runner_smoke \
  --max-rollout-steps 96 \
  --seed-count 1 \
  --device cpu
```

## Result

Run directory:

```text
runs/m1511_decisive_history_bounded_runner_smoke
```

Summary:

```text
spec_count: 6
source_family_count: 6
max_rollout_steps: 96
trace_row_count: 525
snapshot_row_count: 30
rollout_success_count: 6
rollout_failure_count: 0
guardrail_violation_count: 0
```

All six source families reached the reveal, decision, and post-decision
windows:

```text
t4_actuator_delay_response
t4_capability_step_temporal
t4_staged_warmup_capability
t5_boundary_axis_retarget
t5_high_speed_close_obstacle
t5_near_boundary_warmup
```

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_decisive_history_bounded_runner.py -q
6 passed
```

## Guardrails

```text
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

## Interpretation

M1511 proves that the current simulator and fixed M1362 policy can produce
bounded source traces for all six decisive-history source families. This is
important plumbing evidence because M1508 materialization now has real trace
artifacts available for a later audit.

It does not yet prove:

```text
real T4/T5 candidate existence;
same-current same-recent older-history necessity;
wrong-history or delayed-history margin degradation;
level3 online self-identification;
policy superiority;
training corpus validity.
```

The next step must audit trace quality before any candidate materialization.

## Next

```text
m1512-paper-route-decisive-history-bounded-runner-result-audit
```

M1512 should inspect the trace and snapshot artifacts, source-family terminal
patterns, label distribution, margins, and any early signs of candidate
materialization eligibility. It should route either to measured candidate
materialization or to env-hook/runner repair.
