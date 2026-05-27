# M1076 V4 Public Base Medium PPO Contract Clean Full Public Gate

## Purpose

M1076 runs the expanded full public gate on the M1075-selected contract-clean
projection candidate:

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

It does not run PPO, train the actor, promote, or use private holdout.

## Result

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

The candidate passes the full expanded public gate stack.

## Exact And Contract Gate

```text
full_exact_contract_gate_pass: true
allowed_surface_contract_pass: true
changed_parameter_count: 4
changed_parameter_names:
  actor_mean.bias
  actor_mean.weight
  response_context_fusion.0.bias
  response_context_fusion.0.weight
combined_anchor_total_loss: 0.00000934395
combined_anchor_m267_loss: 0.0000361964
combined_anchor_m183_row16_loss: 0.00000263083
```

M1076 preserves the P0 actor-input contract and the allowed changed-parameter
surface.

## Proof Gates

Old public replay surfaces:

```text
m183_m168: 16 / 16 success drops retained
m183_m170: 17 / 17 success drops retained
m193_m189: 14 / 14 success drops retained
m212_m204: 17 / 17 success drops retained
m223_m219: 17 / 17 success drops retained
m267_m264: 17 / 17 success drops retained
```

M1061 family-intersection gate:

```text
replay_gates_passed: 3 / 3
failed_replay_gates: []
```

Source-diverse gate:

```text
current_m333_surface: 17 / 17
m317_continuity_surface: 17 / 17
m314_continuity_surface: 17 / 17
```

## Generalization And Behavior

Fresh/OOD success rates are retained:

```text
fresh seed 103900: 0.8671875 -> 0.8671875
fresh seed 103901: 0.87109375 -> 0.87109375
moderate OOD seed 103920: 0.640625 -> 0.640625
```

Fresh/OOD mean clearance margin deltas are small and positive:

```text
fresh seed 103900: +0.000237061954
fresh seed 103901: +0.000237782609
moderate OOD seed 103920: +0.000069378202
```

Behavior seeds retain candidate success and reset/zero-all ordering:

```text
9505: 0.8625 -> 0.8625
9506: 0.8625 -> 0.8625
103930: 0.8375 -> 0.8375
103931: 0.8250 -> 0.8250
```

## Interpretation

M1076 resolves the M1074 contract artifact. The M1075-selected candidate is a
contract-clean projection from the current public-gate base. It improves the
repair/proof surface enough to pass exact and replay gates while retaining
fresh/OOD and behavior metrics.

This is not a medium-PPO performance claim. The candidate does not show broad
success-rate lift over the current base; it is better described as public-gate
proof hardening before the next PPO proposal.

## Decision

```text
medium_ppo_contract_clean_full_public_gate_pass_route_to_readiness_synthesis
```

Next:

```text
m1077-v4-public-base-medium-ppo-readiness-synthesis
```
