# M1045 V4 Public Base Combined Active-Set Guarded PPO Promotion Audit

## Purpose

M1045 audits whether the M1044 raw guarded PPO checkpoint should replace the
combined active-set base as the current public-gate base.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or claim multi-seed/long-run PPO stability.

## Candidate And Previous Base

Promoted candidate:

```text
runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
```

Previous public-gate base:

```text
runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
```

PPO config:

```text
configs/ppo_m1044_combined_active_set_guarded_smoke.json
```

## Evidence Reviewed

M1044 PPO/run status:

```text
result_class: combined_active_set_guarded_ppo_raw_candidate
ppo_returncode: 0
training_metrics_finite: true
raw_checkpoint_exists: true
actor_inputs_changed: false
training_started: true
ppo_used: true
private_holdout_used: false
promoted: false
```

Exact and combined active-set evidence:

```text
M997 action_l2_mean: 0.003190
M997 action_l2_max: 0.012716
M997 total_loss_improvement: 0.005033
M297 delta vs base: 0.000000
M270 delta vs base: 0.000000
combined anchor total loss: 0.000006316
combined M267 loss: 0.000028293
combined M183 row16 loss: 0.000000821
full exact contract gate: true
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

Hard-row evidence:

```text
M267/M264 row15:
  normal_success: true
  wrong_history_success: false
  normal_margin: 0.005731
  wrong_history_margin: -0.000847

M183/M170 row16:
  normal_success: true
  wrong_history_success: false
  normal_margin: 0.000467
  wrong_history_margin: -0.006022
```

Source-diverse diagnostics:

```text
current_m333_surface: 17 / 17 success drops retained
m317_continuity_surface: 17 / 17 success drops retained
m314_continuity_surface: 17 / 17 success drops retained
```

Fresh public and moderate-OOD public checks:

```text
fresh_public seed 103900:
  base success: 0.867188
  raw success: 0.867188
  margin delta: +0.000181

fresh_public seed 103901:
  base success: 0.871094
  raw success: 0.871094
  margin delta: +0.000181

moderate_ood seed 103920:
  base success: 0.640625
  raw success: 0.640625
  margin delta: +0.000218
```

Behavior/ablation retention:

```text
seeds: 9505, 9506, 103930, 103931
raw normal success matches previous base on all seeds
normal >= reset >= zero_all ordering retained on all seeds
```

## Promotion Decision

Decision:

```text
promote_public_gate_base
```

The M1044 raw PPO checkpoint replaces the M1038 combined active-set checkpoint
as the current public-gate base:

```text
runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
```

Rationale:

```text
1. PPO completed and training metrics are finite.
2. The P0 actor-input contract is preserved.
3. Exact M997/M297/M270/combined-active-set gates pass.
4. M267/M264 row15 wrong-history failure is retained.
5. M183/M170 row16 normal-history success is retained.
6. All six public proof replay surfaces pass.
7. Source-diverse protected diagnostics pass.
8. Fresh public and moderate-OOD checks do not regress success or termination.
9. Behavior/ablation ordering is retained.
10. Promotion is scoped to public-gate base status only.
```

## Scope Limits

This promotion does not claim:

```text
multi-seed PPO repeatability;
long-run PPO stability;
private holdout generalization;
paper-level statistical evidence;
real-vehicle transfer;
full scenario-distribution benchmark completion.
```

The next PPO step remains blocked until post-promotion synthesis decides
whether to repeat smoke PPO with fresh seeds, run longer PPO escalation, refresh
public proof surfaces, or audit overfit risk.

## Superseded Base

The M1038 combined active-set checkpoint becomes the previous public-gate base:

```text
runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
```

Candidate B, M974, M964 alpha `1.0`, and M399 alpha `0.05` remain older lineage
points.

## Next Blocker

After promotion, the next step is a post-promotion synthesis milestone. It
should decide whether to:

```text
1. repeat guarded PPO smoke with fresh PPO seeds;
2. escalate to a short multi-seed PPO ladder;
3. refresh public proof surfaces first;
4. stop and audit public-gate overfit risk.
```

## Decision

```text
combined_active_set_guarded_ppo_promote_public_gate_base
```

Next:

```text
m1046-v4-public-base-guarded-ppo-post-promotion-synthesis
```
