# M1252 Paper-Route Capability-Separable Proposal Margin-Restoration Smoke

## Summary

M1252 runs the one targeted no-training margin-restoration smoke admitted by
M1251.

Decision:

```text
proposal_margin_restoration_near_miss_persists_route_to_source_variable_audit
```

The infrastructure passed, but the source-positive gate still did not pass:

```text
accepted_separable_pairs: 0
result_class: action_divergent_low_regret
```

The near-miss improved again, but remained slightly nonviable:

```text
M1250 pair 5 pair_min_best_margin: -0.0018868557
M1252 pair 5 pair_min_best_margin: -0.0006610772
```

M1251's stop rule now fires: do not continue expanding this source run. Audit
the trajectory proposal source variable before another source change.

## Final Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_separable_source_constructor \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/m1236_extreme_fault_timing_repair_smoke.json \
  --pairing-mode cross_fault \
  --seed-start 124600 \
  --seed-count 4 \
  --max-pairs 8 \
  --max-pairs-per-seed 4 \
  --max-pairs-per-family-pair 8 \
  --candidate-mode trajectory_proposal \
  --sequence-length 4 \
  --proposal-count-per-condition 32 \
  --proposal-seed 125200 \
  --proposal-steer-scale 0.45 \
  --proposal-brake-scale 0.45 \
  --proposal-throttle-scale 0.25 \
  --source-window-mode viability_band_relocation \
  --target-min-best-margin 0.005 \
  --target-max-best-margin 0.08 \
  --max-relocation-candidates 16 \
  --fine-relocation \
  --fine-parent-count 1 \
  --max-continuation-steps 18 \
  --min-best-action-l2 0.12 \
  --min-cross-regret-margin 0.02 \
  --device auto \
  --run-dir runs/m1252_capability_separable_proposal_margin_restoration_smoke
```

## Final Result

Artifact:

```text
runs/m1252_capability_separable_proposal_margin_restoration_smoke/summary.json
```

Key metrics:

```text
matched_pair_count: 8
trajectory_proposals: 552
trajectory_proposal_rollouts: 1104
relocation_candidates: 128
coarse_relocation_candidates: 64
fine_relocation_candidates: 64
near_boundary_viability_pairs: 0
accepted_separable_pairs: 0
best_actions_diverged_pairs: 6
low_regret_pairs: 7
unique_matched_fault_family_pairs: 2
unique_matched_seeds: 2
result_class: action_divergent_low_regret
actor_parameters_changed: false
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
```

Selected-pair rejection reasons:

```text
best_candidate_not_viable: 6
best_actions_too_close: 2
```

## Key Row

M1252's strongest selected row:

```text
pair_id: 5
seed: 124601
family_pair: global_mu_drop->brake_authority_drop
relocation_stage: fine
relocation_id: 11
best_action_l2: 0.3543319404
cross_regret_A: 0.2376237919
cross_regret_B: 0.0226062003
pair_min_best_margin: -0.0006610772
margin_A_best_A: -0.0006610772
margin_B_best_B: -0.0000902261
rejection_reason: best_candidate_not_viable
```

This is closer to accepted than M1250 but still fails own-branch viability.

## Interpretation

M1252 supports:

```text
targeted proposal/source repair can move the near-miss closer to viability;
the current run still cannot produce accepted source-positive rows;
thresholds should remain unchanged;
training remains blocked.
```

M1252 does not support:

```text
self-identification;
history necessity;
checkpoint promotion;
PPO readiness;
paper-level evidence.
```

The result is a useful near-miss, but M1251 explicitly allowed only one
targeted repair before an audit. Continuing with more proposal seeds or budgets
now would risk local gate chasing.

## Next

```text
m1253-paper-route-capability-separable-trajectory-proposal-source-variable-audit
```
