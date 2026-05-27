# M1074 V4 Public Base Medium PPO Repair Projection Full Public Gate

## Purpose

M1074 runs the expanded full public gate on the M1073 no-PPO repaired projection
candidate:

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_line_row16x4_s40_a1.pt
```

It does not run PPO, promote, or use private holdout.

## Result

```text
result_class: candidate_b_combined_active_set_full_public_gate_contract_artifact
exact_pass: false
proof_pass: true
family_intersection_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
actor_inputs_changed: false
allowed_surface_contract_pass: false
promoted: false
private_holdout_used: false
```

M1074 is rejected, but not because the repaired candidate washed out closed-loop
proof. It is rejected because the selected checkpoint violates the allowed
parameter-surface contract for this repair family.

## Exact Contract Failure

```text
full_exact_contract_gate_pass: false
allowed_surface_contract_pass: false
actor_inputs_changed: false
M297/M270 exact pass: true
combined_anchor_total_loss: 0.00000944194
combined_anchor_m267_loss: 0.0000365366
combined_anchor_m183_row16_loss: 0.00000266829
```

Allowed changed prefixes:

```text
actor_mean.
response_context_fusion.0.
```

Actual changed parameter groups included:

```text
actor_mean
context_encoder
critic
online_gru_cell
response_context_fusion.0
response_encoder
response_prediction_head
```

This happened because the selected `line_row16x4_s40_a1` candidate inherits the
M1069 raw PPO proposal's broader parameter movement. The actor input contract is
unchanged, but the repair-surface contract is not.

## Proof Gates

All old public proof replay surfaces passed:

```text
m183_m168: 16 / 16 success drops retained
m183_m170: 17 / 17 success drops retained
m193_m189: 14 / 14 success drops retained
m212_m204: 17 / 17 success drops retained
m223_m219: 17 / 17 success drops retained
m267_m264: 17 / 17 success drops retained
```

The M1061 family-intersection gate passed:

```text
replay_gates_passed: 3 / 3
failed_replay_gates: []
```

The source-diverse gate passed:

```text
current_m333_surface: 17 / 17
m317_continuity_surface: 17 / 17
m314_continuity_surface: 17 / 17
```

Fresh/OOD and behavior gates also passed.

## Interpretation

M1074 shows that M1072/M1073 fixed the closed-loop proof-washout problem for the
selected candidate. The remaining blocker is not family-intersection proof, old
public replay, source-diverse replay, fresh/OOD, or behavior.

The blocker is candidate cleanliness:

```text
the full gate selected a first-replay-safe candidate whose parameter movement is
too broad for the allowed projection surface.
```

M1073's candidate table already contains contract-clean alternatives. In
particular:

```text
m1031_base_row16x4_s40_a1
checkpoint:
  runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
changed_parameter_count: 4
changed_parameter_names:
  actor_mean.bias
  actor_mean.weight
  response_context_fusion.0.bias
  response_context_fusion.0.weight
exact_gate_pass: true
exact_m297_delta_vs_base: -0.000085235
exact_m270_delta_vs_base: -0.000068545
combined_anchor_total_loss: 0.00000934395
```

That candidate is lower-ranked by the previous projection selector but appears
better aligned with the current full-gate contract.

## Decision

```text
medium_ppo_projection_full_gate_contract_artifact_route_to_contract_clean_candidate_audit
```

Next:

```text
m1075-v4-public-base-medium-ppo-contract-clean-candidate-audit
```
