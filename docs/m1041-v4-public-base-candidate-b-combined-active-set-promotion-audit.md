# M1041 V4 Public Base Candidate B Combined Active-Set Promotion Audit

## Purpose

M1041 audits whether the M1038 combined active-set full public-gate candidate
should replace Candidate B as the current public-gate base.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or claim paper-level/real-vehicle generalization.

## Candidate And Previous Base

Promoted candidate:

```text
runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
```

Previous public-gate base:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

Candidate source:

```text
M1038 selected base_row16x4_s40 alpha 0.15
```

## Evidence Reviewed

M1038 combined active-set repair/projection probe:

```text
selected candidate: m1031_base_row16x4_s40_a0_15
M997 action_l2_mean: 0.002198
M997 action_l2_max: 0.002520
M297 delta: -0.000020
M270 delta: -0.000001
M267/M264 first replay: pass, row15 retained
M183/M170 first replay: pass, row16 retained
training_started: false
ppo_used: false
private_holdout_used: false
promoted: false
```

M1040 full public gate:

```text
result_class: candidate_b_combined_active_set_full_public_gate_candidate
exact_pass: true
proof_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
actor_inputs_changed: false
training_started: false
ppo_used: false
private_holdout_used: false
promoted: false
```

Exact and trainable-surface evidence:

```text
allowed changed prefixes:
  actor_mean.
  response_context_fusion.0.

changed parameters:
  actor_mean.bias
  actor_mean.weight
  response_context_fusion.0.bias
  response_context_fusion.0.weight

M997 temporal retention: pass
M297/M270 exact no-regression: pass
combined active-set loss: pass
```

Proof replay evidence:

```text
m183_m168: 16 / 16 success drops retained
m183_m170: 17 / 17 success drops retained
m193_m189: 14 / 14 success drops retained
m212_m204: 17 / 17 success drops retained
m223_m219: 17 / 17 success drops retained
m267_m264: 17 / 17 success drops retained
```

Source-diverse diagnostics:

```text
current_m333_surface: 17 / 17 success drops retained
m317_continuity_surface: 17 / 17 success drops retained
m314_continuity_surface: 17 / 17 success drops retained
```

Fresh public and moderate-OOD non-regression:

```text
fresh_public seed 103900:
  base success: 0.867188
  candidate success: 0.867188
  margin delta: -0.000915

fresh_public seed 103901:
  base success: 0.871094
  candidate success: 0.871094
  margin delta: -0.000914

moderate_ood seed 103920:
  base success: 0.640625
  candidate success: 0.640625
  margin delta: -0.000653
```

Behavior/ablation retention:

```text
seeds: 9505, 9506, 103930, 103931
candidate normal success matches previous base on all seeds
normal >= reset >= zero_all ordering retained on all seeds
```

## Promotion Decision

Decision:

```text
promote_public_gate_base
```

The M1038 selected checkpoint replaces Candidate B as the current public-gate
base:

```text
runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
```

Rationale:

```text
1. The P0 actor-input contract is preserved.
2. The trainable surface remains limited to actor_mean and response_context_fusion.0.
3. M997 temporal retention and M297/M270 exact no-regression pass.
4. M267/M264 row15 and M183/M170 row16 active-set blockers both remain retained.
5. All six public proof replay surfaces pass.
6. Source-diverse protected diagnostics pass.
7. Fresh public and moderate-OOD evaluations do not regress success or termination rates.
8. Behavior/ablation ordering is retained.
9. The promotion is scoped to public-gate base status only.
```

## Scope Limits

This promotion does not claim:

```text
private holdout generalization;
paper-level statistical evidence;
real-vehicle transfer;
long-run PPO stability;
full scenario-distribution benchmark completion;
closed-loop self-identification proof beyond registered public gates.
```

PPO remains blocked until a post-promotion synthesis/readiness milestone
decides the next controlled route.

## Superseded Base

Candidate B becomes the previous public-gate base:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

M974, M964 alpha `1.0`, and M399 alpha `0.05` remain older lineage points.

## Next Blocker

After promotion, the next step is a post-promotion synthesis milestone. It
should decide whether to:

```text
1. run guarded PPO readiness from the new public-gate base;
2. refresh post-promotion public proof surfaces first;
3. run additional public generalization before PPO;
4. stop and audit public-gate overfit risk.
```

## Decision

```text
candidate_b_combined_active_set_promote_public_gate_base
```

Next:

```text
m1042-v4-public-base-combined-active-set-post-promotion-synthesis
```
