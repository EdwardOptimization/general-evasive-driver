# M1064 V4 Public Base Family-Intersection Public Gate Implementation

## Purpose

M1064 implements the reusable public proof gate wrapper designed in M1063. The
gate turns the M1061 family-intersection corpora into a standard source-to-
candidate replay bundle that can be inserted before medium PPO.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or promote a checkpoint.

## Implementation

Added:

```text
src/autodrift/family_intersection_public_gate.py
tests/test_family_intersection_public_gate.py
```

The wrapper reuses `boundary_outcome_replay_gate` and adds:

```text
source policy / corpus label validation
candidate-label collision checks
checkpoint and corpus existence checks
actor input signature check
three source-to-candidate replay gate execution
aggregate pass/fail summary
```

It intentionally does not duplicate rollout logic.

## Gate Definition

For a candidate checkpoint, the wrapper runs:

```text
short61049 corpus:
  baseline: short61049
  candidate: candidate_policy

short61050 corpus:
  baseline: short61050
  candidate: candidate_policy

short61051 corpus:
  baseline: short61051
  candidate: candidate_policy
```

Thresholds:

```text
max_normal_success_drop: 0.0
max_normal_margin_regression: 0.005
max_margin_gap_regression: 0.001
max_success_drop_count_regression: 0
max_continuation_steps: 60
```

The aggregate passes only if:

```text
replay_gates_passed == replay_gate_count
actor_inputs_changed == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
```

## Current-Base Validation

Command class:

```text
python -m autodrift.family_intersection_public_gate ...
```

Run:

```text
runs/m1064_family_intersection_public_gate_current_base
```

Candidate:

```text
current_base = runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
```

Result:

```text
result_class: family_intersection_public_gate_pass
overall_pass: true
replay_gate_count: 3
replay_gates_passed: 3
actor_inputs_changed: false
failure_types: none
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
```

Replay rows:

```text
short61049 -> current_base:
  rows: 25
  baseline_success_drop_count: 25
  candidate_success_drop_count: 25
  gate_pass: true

short61050 -> current_base:
  rows: 27
  baseline_success_drop_count: 27
  candidate_success_drop_count: 27
  gate_pass: true

short61051 -> current_base:
  rows: 27
  baseline_success_drop_count: 27
  candidate_success_drop_count: 27
  gate_pass: true
```

Artifacts:

```text
runs/m1064_family_intersection_public_gate_current_base/summary.json
runs/m1064_family_intersection_public_gate_current_base/replay_gate_summary.csv
runs/m1064_family_intersection_public_gate_current_base/diagnostic_summary.csv
```

## Classification

```text
result_class: family_intersection_public_gate_pass
failure_types: none
```

This validates that the current public-gate base passes the new M1061
family-intersection public proof gate when evaluated as a candidate checkpoint.

## Decision

```text
family_intersection_public_gate_implementation_pass_route_to_stack_integration
```

Next:

```text
m1065-v4-public-base-family-intersection-stack-integration
```

M1065 should integrate this wrapper into the guarded PPO/full public gate stack
so future PPO candidates cannot reach medium PPO or promotion while breaking
the refreshed family-intersection proof surface.
