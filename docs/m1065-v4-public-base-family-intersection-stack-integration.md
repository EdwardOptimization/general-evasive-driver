# M1065 V4 Public Base Family-Intersection Stack Integration

## Purpose

M1065 integrates the M1064 family-intersection public gate into the guarded
PPO/full public gate stack and validates the new proof tier without PPO.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or promote a checkpoint.

## Code Integration

Updated:

```text
src/autodrift/candidate_b_combined_active_set_full_public_gate.py
tests/test_candidate_b_combined_active_set_full_public_gate.py
```

The full public gate now has default M1061 family-intersection sources:

```text
short61049: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
short61050: runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt
short61051: runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

and default M1061 source corpora:

```text
runs/m1061_short61049_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv
runs/m1061_short61050_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv
runs/m1061_short61051_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv
```

`run_combined_active_set_full_public_gate` now invokes
`run_family_intersection_public_gate` by default after the old public replay
and source-diverse proof checks, and before generalization and behavior
evaluation. A failure in this new gate is classified as:

```text
candidate_b_combined_active_set_full_public_gate_public_replay_washout
failure_types: proof_washout
```

This means future guarded PPO proposals cannot pass the full public gate while
breaking the refreshed M1061 family-intersection proof surface.

## No-PPO Current-Base Validation

The full public gate's exact-contract path is designed for a changed candidate
checkpoint. For current-base no-PPO validation, M1065 validates the newly
integrated proof tier directly with the M1064 wrapper.

Run:

```text
runs/m1065_expanded_stack_family_intersection_preflight
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
failed_replay_gates: []
actor_inputs_changed: false
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
runs/m1065_expanded_stack_family_intersection_preflight/summary.json
runs/m1065_expanded_stack_family_intersection_preflight/replay_gate_summary.csv
```

## Gate Order

Expanded guarded PPO/full public gate order:

```text
PPO proposal
  -> exact active-set checks
  -> old public replay proof gates
  -> source-diverse diagnostics
  -> M1061 family-intersection public gate
  -> fresh/OOD generalization
  -> behavior retention
```

The M1061 gate is a proof-tier gate. It blocks later generalization, behavior,
promotion, and medium-PPO escalation if refreshed wrong-history proof rows are
lost.

## Classification

```text
result_class: family_intersection_public_gate_pass
failure_types: none
```

M1065 proves the integration point exists and that the current public-gate base
passes the newly integrated proof tier. It does not prove medium PPO stability.

## Decision

```text
family_intersection_stack_integration_pass_route_to_pre_medium_readiness_synthesis
```

Next:

```text
m1066-v4-public-base-pre-medium-ppo-readiness-synthesis
```

M1066 should synthesize the short-PPO promotion, refreshed family surface, and
expanded gate stack before designing any medium PPO run.
