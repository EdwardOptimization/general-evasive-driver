# M1040 V4 Public Base Candidate B Combined Active-Set Full Public Gate

## Purpose

M1040 runs the full public proof/generalization/behavior gate for the M1038
combined active-set candidate before any promotion decision.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or promote a checkpoint.

## Command

```bash
rm -rf runs/m1040_candidate_b_combined_active_set_full_public_gate && \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.candidate_b_combined_active_set_full_public_gate \
  --run-dir runs/m1040_candidate_b_combined_active_set_full_public_gate \
  --device auto
```

## Candidate And Baseline

Baseline public-gate base:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

Candidate:

```text
runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
```

Source:

```text
M1038 selected base_row16x4_s40 alpha 0.15
```

## Contract

Allowed changed parameter prefixes for this branch:

```text
actor_mean.
response_context_fusion.0.
```

Observed changed parameters:

```text
actor_mean.bias
actor_mean.weight
response_context_fusion.0.bias
response_context_fusion.0.weight
```

Still forbidden and unchanged:

```text
actor input config
response/context encoders
GRU/recurrent state
critic
log_std
```

Actor inputs changed:

```text
false
```

## Result

Run result:

```text
result_class: candidate_b_combined_active_set_full_public_gate_candidate
exact_pass: true
proof_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
failure_types: none
training_started: false
ppo_used: false
private_holdout_used: false
promoted: false
```

Summary artifact:

```text
runs/m1040_candidate_b_combined_active_set_full_public_gate/summary.json
```

## Exact Contract

M997 temporal retention, M297/M270 exact no-regression, and combined active-set
loss checks all pass.

```text
M997 action_l2_mean: 0.002198
M997 action_l2_max: 0.002520
M297 delta vs base: 0.000000
M270 delta vs base: 0.000000
M297/M270 exact pass: true
combined anchor total loss: 0.000006485
combined M267 loss: 0.000028552
combined M183 row16 loss: 0.000000968
allowed surface contract pass: true
```

## Proof Replay Gates

All six public replay surfaces pass.

```text
m183_m168: 16 / 16 success drops retained
m183_m170: 17 / 17 success drops retained
m193_m189: 14 / 14 success drops retained
m212_m204: 17 / 17 success drops retained
m223_m219: 17 / 17 success drops retained
m267_m264: 17 / 17 success drops retained
```

The candidate preserves wrong-history sensitivity on these public surfaces.
Normal-margin mean deltas are slightly negative, around `-0.001`, while
margin-gap mean deltas stay slightly positive, around `+0.000026`.

## Source-Diverse Diagnostics

The source-diverse protected replay diagnostics also pass.

```text
current_m333_surface: 17 / 17 success drops retained
m317_continuity_surface: 17 / 17 success drops retained
m314_continuity_surface: 17 / 17 success drops retained
```

The old `9944|perturbed|28|28` neighborhood remains diagnostic-only. It is not
used as a single-key veto in this milestone.

## Generalization

Fresh public and moderate-OOD evaluations retain success and termination rates
relative to the baseline.

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

These are public checks, not private holdout or paper-level evidence.

## Behavior And Ablation

Behavior seeds pass and preserve the expected ordering:

```text
normal >= reset >= zero_all
```

Results:

```text
seed 9505: normal 0.8625, reset 0.8500, zero_all 0.8000
seed 9506: normal 0.8625, reset 0.8500, zero_all 0.8000
seed 103930: normal 0.8375, reset 0.8125, zero_all 0.8000
seed 103931: normal 0.8250, reset 0.8000, zero_all 0.7875
```

Candidate normal success matches the baseline on all behavior seeds.

## Interpretation

M1040 upgrades the M1038 selected checkpoint from first-replay candidate to
full public-gate candidate. The evidence supports a separate promotion audit.

It does not yet support:

```text
public-base promotion;
private holdout generalization;
paper-level statistical claims;
long-run PPO stability;
real-vehicle transfer;
full scenario-distribution benchmark completion.
```

## Decision

Decision:

```text
candidate_b_combined_active_set_full_public_gate_candidate_route_to_promotion_audit
```

Next:

```text
m1041-v4-public-base-candidate-b-combined-active-set-promotion-audit
```
