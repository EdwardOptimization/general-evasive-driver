# M1078 V4 Public Base Contract Clean Projection Promotion Audit

## Purpose

M1078 audits whether the M1076 contract-clean projection candidate should become
the next public-gate base.

This milestone does not train, run PPO, or use private holdout.

## Candidate

Previous public-gate base:

```text
runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
```

Candidate:

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

## Evidence

M1076 classified the candidate as:

```text
result_class: candidate_b_combined_active_set_full_public_gate_candidate
actor_inputs_changed: false
allowed_surface_contract_pass: true
exact_pass: true
proof_pass: true
family_intersection_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
ppo_used: false
promoted: false
private_holdout_used: false
```

Proof replay coverage:

```text
old public replay gates: 6 / 6
M1061 family-intersection replay gates: 3 / 3
source-diverse replay gates: 3 / 3
```

Fresh/OOD and behavior success rates were retained:

```text
fresh seed 103900: 0.8671875 -> 0.8671875
fresh seed 103901: 0.87109375 -> 0.87109375
moderate OOD seed 103920: 0.640625 -> 0.640625
behavior seeds: no success-rate regression
```

The candidate is contract-clean:

```text
changed_parameter_count: 4
changed_parameter_names:
  actor_mean.bias
  actor_mean.weight
  response_context_fusion.0.bias
  response_context_fusion.0.weight
```

## Scope

Promotion scope is limited:

```text
public-gate base: yes
proof-base hardening: yes
medium-PPO performance improvement: no
long-run PPO stability: no
private-holdout evidence: no
paper-level generalization: no
real-vehicle claim: no
```

The reason to promote is not broad success-rate lift. The reason is that the
candidate is a contract-clean proof-hardening projection from the current base
that passes the expanded public gate stack after M1069 exposed medium-PPO proof
washout.

## Decision

Promote the M1076 candidate as the current public-gate base:

```text
contract_clean_projection_promote_public_gate_base
```

New public-gate base:

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

Previous public-gate base:

```text
runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
```

Next:

```text
m1079-v4-public-base-contract-clean-post-promotion-synthesis
```
