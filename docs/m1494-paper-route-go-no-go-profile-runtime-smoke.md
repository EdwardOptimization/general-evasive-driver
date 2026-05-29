# M1494 Paper-Route Go/No-Go Profile Runtime Smoke

## Summary

M1494 runs the no-training runtime smoke over the refreshed 12-profile
go/no-go config set from M1493.

Decision:

```text
go_no_go_profile_runtime_smoke_pass_admit_one_seed_smoke
```

Result class:

```text
controller_profile_runtime_smoke_pass
```

This milestone does not train, run PPO, run replay, run performance evaluation,
promote a checkpoint, use private holdout, export corpus, or change actor
inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.controller_profile_runtime_smoke \
  --config-dir configs/paper_route_corrected_profiles \
  --config-glob 'm1207_*.json' \
  --seed 149400 \
  --run-dir runs/m1494_go_no_go_profile_runtime_smoke
```

## Result

Artifact:

```text
runs/m1494_go_no_go_profile_runtime_smoke/summary.json
```

Summary:

```text
result_class: controller_profile_runtime_smoke_pass
config_count: 12
all_configs_instantiated: true
contract_ok: true
model_forward_ok: true
l0_mask_observed: true
unmasked_profiles_unchanged: true
current_tiled_profile_count: 4
current_tiled_profiles_observed: true
corrected_reset_profile_count: 1
corrected_reset_policy_routing_ok: true
training_started: false
optimizer_started: false
ppo_used: false
candidate_replay_started: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
```

Profiles validated:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L2_window_50
L2_window_50_current_tiled
L2_window_100
L2_window_100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

## Runtime Checks

The smoke verifies:

```text
L0 previous-command masking is observed;
unmasked profiles remain unchanged;
all four L2 current-tiled controls repeat the current frame at runtime;
L3_reset_control_corrected routes every-step reset semantics;
all model forwards succeed;
all P0 human-view/no-wheel/no-oracle contract checks pass.
```

## Interpretation

Supported:

```text
The full 12-profile config set is runtime-valid.
The profile masks and controls needed for a fair go/no-go matrix are active.
The branch can proceed to a one-seed fixed-budget plumbing smoke.
```

Unsupported:

```text
profile ranking;
finite-window history necessity;
online-GRU hidden advantage;
level3 self-identification;
promotion;
private holdout generalization.
```

Runtime smoke is not performance evidence. It only proves that the comparison
harness can instantiate and route the required controls before training.

## Next Route

Admit one-seed fixed-budget plumbing smoke:

```text
m1495-paper-route-go-no-go-profile-one-seed-smoke
```

Candidate command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.corrected_profile_pilot \
  --config-dir configs/paper_route_corrected_profiles \
  --config-glob 'm1207_*.json' \
  --run-dir runs/m1495_go_no_go_profile_one_seed_smoke \
  --training-seed-base 149500 \
  --seed-offsets 0 \
  --eval-seed-base 149600 \
  --eval-episodes 32 \
  --device cpu
```

M1495 should be interpreted as plumbing only. It should route to an audit before
any 3-seed pilot, private holdout, promotion, or profile-ranking claim.

## Guardrails

```text
training_started: false
evaluation_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```
