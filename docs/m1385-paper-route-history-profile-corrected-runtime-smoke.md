# M1385 Paper-Route History-Profile Corrected Runtime Smoke

## Purpose

M1385 runs the no-training corrected-profile runtime smoke admitted by M1384.
It verifies that all corrected L0/L1/L2/L3 profile configs instantiate and that
the required current-tiled and corrected reset-control metadata are observed
before any fixed-budget profile training.

M1385 does not train, evaluate checkpoints, run PPO, promote, use private
holdout, export a corpus, change actor inputs, or claim a profile ranking.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.controller_profile_runtime_smoke \
  --config-dir configs/paper_route_corrected_profiles \
  --config-glob 'm1207_*.json' \
  --seed 138500 \
  --run-dir runs/m1385_history_profile_corrected_runtime_smoke
```

## Result

Artifact:

```text
runs/m1385_history_profile_corrected_runtime_smoke/summary.json
```

Summary:

```text
result_class: controller_profile_runtime_smoke_pass
config_count: 8
all_configs_instantiated: true
contract_ok: true
model_forward_ok: true
l0_mask_observed: true
current_tiled_profile_count: 2
current_tiled_profiles_observed: true
corrected_reset_profile_count: 1
corrected_reset_policy_routing_ok: true
unmasked_profiles_unchanged: true
training_started: false
optimizer_started: false
ppo_used: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
```

Profiles:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L3_online_gru
L3_reset_control_corrected
```

## Interpretation

M1385 confirms the runtime prerequisites for a one-seed fixed-budget smoke:

```text
1. the corrected profile config set still instantiates;
2. L0 previous-command masking is observed;
3. L2 current-tiled history transforms are observed;
4. corrected L3 reset-control metadata is present and routed;
5. no forbidden training or promotion path started.
```

This is infrastructure readiness only. It is not profile-performance evidence.

## Decision

Decision:

```text
history_profile_corrected_runtime_smoke_pass_admit_one_seed_smoke
```

Next:

```text
m1386-paper-route-history-profile-one-seed-fixed-budget-smoke
```

M1386 may run the one-seed fixed-budget profile training/eval smoke using the
fixed command from M1384. It should still make only a plumbing/training-readiness
claim, not an architecture ranking.

## Guardrails

M1385 performs no training, checkpoint evaluation, PPO, actor update, checkpoint
mutation, promotion, private holdout, threshold relaxation, actor-input
expansion, corpus export, high-fidelity claim, paper-level profile-ranking
claim, or level3 self-identification claim.
