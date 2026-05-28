# M1250 Paper-Route Capability-Separable Trajectory Proposal Source Smoke

## Summary

M1250 implements and runs the first bounded no-training condition-wise
trajectory proposal source smoke.

Decision:

```text
trajectory_proposal_source_near_miss_route_to_result_audit
```

The infrastructure passed, but the source-positive gate still did not pass:

```text
accepted_separable_pairs: 0
result_class: action_divergent_low_regret
```

The result is not a dead end. Compared with M1247, trajectory proposals
improved the best near-positive row:

```text
M1247 pair 5 pair_min_best_margin: -0.0048001855
M1250 pair 5 pair_min_best_margin: -0.0018868557
M1250 pair 5 min two-sided cross-regret: 0.0239608733
```

This means the proposal source found branch-specific trajectory differences,
but own-branch viability remains slightly below zero.

## Implementation

M1250 extends `src/autodrift/capability_separable_source_constructor.py` with:

```text
--candidate-mode trajectory_proposal
--proposal-count-per-condition
--proposal-seed
--proposal-steer-scale
--proposal-throttle-scale
--proposal-brake-scale
```

The new mode builds a no-training proposal union:

```text
A-origin proposals around condition A's deterministic action
B-origin proposals around condition B's deterministic action
shared proposals around the averaged base action
```

Proposal metadata is written to source artifacts only. It is not actor input.

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
  --proposal-count-per-condition 24 \
  --proposal-seed 125000 \
  --proposal-steer-scale 0.45 \
  --proposal-brake-scale 0.45 \
  --proposal-throttle-scale 0.25 \
  --source-window-mode viability_band_relocation \
  --target-min-best-margin 0.02 \
  --target-max-best-margin 0.5 \
  --max-relocation-candidates 12 \
  --fine-relocation \
  --fine-parent-count 1 \
  --max-continuation-steps 18 \
  --min-best-action-l2 0.12 \
  --min-cross-regret-margin 0.02 \
  --device auto \
  --run-dir runs/m1250_capability_separable_trajectory_proposal_source_smoke
```

## Final Result

Artifact:

```text
runs/m1250_capability_separable_trajectory_proposal_source_smoke/summary.json
```

Key metrics:

```text
candidate_pair_count: 204
matched_pair_count: 8
trajectory_proposals: 425
trajectory_proposal_rollouts: 850
relocation_candidates: 96
coarse_relocation_candidates: 64
fine_relocation_candidates: 32
near_boundary_viability_pairs: 1
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

Proposal origins:

```text
A: 200
B: 197
shared: 28
```

Selected-pair rejection reasons:

```text
best_candidate_not_viable: 6
best_actions_too_close: 2
```

## Key Near-Miss

The strongest selected row is pair 5:

```text
pair_id: 5
seed: 124601
family_pair: global_mu_drop->brake_authority_drop
relocation_stage: coarse
relocation_id: 1
best_action_l2: 0.3979088664
cross_regret_A: 0.2439473105
cross_regret_B: 0.0239608733
pair_min_best_margin: -0.0018868557
margin_A_best_A: -0.0018868557
margin_B_best_B: -0.0004172706
rejection_reason: best_candidate_not_viable
```

This row passes the two-sided cross-regret threshold but fails own-branch
viability by a small margin. It is the closest current capability-separable
near-miss.

Some relocation candidates had even larger two-sided regret but were much less
viable, so they are not better source rows.

## Interpretation

M1250 supports:

```text
trajectory proposal source infrastructure works;
condition-wise proposals expose stronger branch-specific action differences
than the fixed lattice;
the current best source remains slightly nonviable;
training remains blocked until accepted rows exist.
```

M1250 does not support:

```text
self-identification;
history necessity;
checkpoint promotion;
PPO readiness;
paper-level evidence.
```

Do not lower the viability or regret thresholds after seeing this result. The
correct next step is a near-miss audit that decides whether to run a targeted
proposal/source repair or pivot again.

## Next

```text
m1251-paper-route-capability-separable-trajectory-proposal-near-miss-audit
```
