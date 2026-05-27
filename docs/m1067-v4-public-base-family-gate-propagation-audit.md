# M1067 V4 Public Base Family Gate Propagation Audit

## Purpose

M1067 audits and fixes a propagation gap found before writing the medium PPO
design. M1065 integrated the M1061 family-intersection gate into the full
public gate, but the guarded PPO wrapper also needs to consume that result so
future PPO proposals are rejected when the refreshed proof surface regresses.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or promote a checkpoint.

## Issue

`run_combined_active_set_full_public_gate` now reports:

```text
family_intersection_pass
family_intersection_summary_json
```

But before M1067, `combined_active_set_guarded_ppo_smoke` only consumed:

```text
exact_pass
proof_pass
source_diverse_pass
generalization_pass
behavior_pass
```

That meant a future PPO proposal could fail the M1061 family-intersection gate
inside the full public gate while the outer guarded PPO wrapper still classified
the proposal using only the older public replay proof result.

## Fix

Updated:

```text
src/autodrift/combined_active_set_guarded_ppo_smoke.py
tests/test_combined_active_set_guarded_ppo_smoke.py
```

The guarded PPO wrapper now:

```text
1. copies family_intersection_summary_json from the full public gate;
2. reads family_intersection_pass from the full public gate summary;
3. exposes family_intersection_pass in its own summary and route_decision row;
4. computes proof_pass as public_replay_pass && family_intersection_pass;
5. classifies family_intersection_pass == false as public_replay_washout.
```

Classification:

```text
combined_active_set_guarded_ppo_public_replay_washout
failure_types: proof_washout
```

## Validation

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_combined_active_set_guarded_ppo_smoke.py \
  tests/test_candidate_b_combined_active_set_full_public_gate.py \
  tests/test_family_intersection_public_gate.py
```

Result:

```text
12 passed
```

The new unit test explicitly verifies:

```text
family_intersection_pass=false
  -> combined_active_set_guarded_ppo_public_replay_washout
```

## Classification

```text
result_class: family_gate_propagation_audit_pass
failure_types: none
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
```

This corrects the implementation gap before any medium PPO design or run.

## Decision

```text
family_gate_propagation_audit_pass_route_to_medium_ppo_design
```

Next:

```text
m1068-v4-public-base-expanded-gate-medium-ppo-design
```

M1068 should now design the conservative medium PPO escalation using the
expanded public gate stack. It should not run PPO.
