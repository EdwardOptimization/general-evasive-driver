# M1493 Paper-Route Go/No-Go Profile Config Refresh Implementation

## Summary

M1493 implements the full go/no-go profile config refresh required by M1492.

Decision:

```text
go_no_go_profile_config_refresh_implemented_admit_runtime_smoke
```

This milestone is infrastructure only. It does not train, run PPO, run replay,
run route evaluation, promote a checkpoint, use private holdout, export a
training corpus, or change actor inputs.

## What Changed

The corrected profile config generator now covers the full M1492 matrix:

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

The previously missing controls are now generated:

```text
L2_window_50_current_tiled
L2_window_100_current_tiled
```

The fixed-budget pilot main-profile set now includes:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L3_online_gru
```

The current-tiled controls remain diagnostics and capacity controls rather than
main profiles.

## Generated Configs

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.corrected_profile_configs \
  --output-dir configs/paper_route_corrected_profiles \
  --run-dir runs/m1493_go_no_go_profile_config_refresh
```

Generated config artifacts:

```text
configs/paper_route_corrected_profiles/m1207_l2_window_50.json
configs/paper_route_corrected_profiles/m1207_l2_window_50_current_tiled.json
configs/paper_route_corrected_profiles/m1207_l2_window_100.json
configs/paper_route_corrected_profiles/m1207_l2_window_100_current_tiled.json
```

Run artifact:

```text
runs/m1493_go_no_go_profile_config_refresh/summary.json
```

Summary:

```text
result_class: corrected_profile_configs_generated
generated_config_count: 12
current_tiled_profiles:
  L2_window_13_current_tiled
  L2_window_25_current_tiled
  L2_window_50_current_tiled
  L2_window_100_current_tiled
corrected_reset_profiles:
  L3_reset_control_corrected
hidden_or_oracle_actor_inputs: false
wheel_or_slip_actor_inputs: false
training_started: false
optimizer_started: false
ppo_used: false
candidate_replay_started: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
```

## Verification

Focused tests:

```bash
python -m pytest tests/test_corrected_profile_configs.py \
  tests/test_corrected_profile_pilot.py \
  tests/test_controller_profile_runtime_smoke.py \
  tests/test_controller_profiles.py -q
```

Result:

```text
23 passed in 2.16s
```

The tests verify:

```text
corrected profile coverage is 12 profiles;
current-tiled controls exist for L2 windows 13, 25, 50, and 100;
current-tiled controls preserve matched observation dimensions and temporal-GRU settings;
forbidden hidden/oracle/wheel/reference input flags remain false;
L3_reset_control_corrected keeps every-step reset-control semantics;
runtime smoke helpers expect 12 corrected configs and 4 current-tiled controls.
```

## Interpretation

Supported:

```text
The full M1492 controller-family config set is now generated.
The missing long-window current-tiled controls are present.
The config layer is ready for no-training runtime smoke.
```

Unsupported:

```text
runtime behavior is not yet validated for the full 12-config set;
no training has run;
no fixed-budget profile ranking is supported;
no finite-window history necessity is supported;
no online-GRU recurrent self-ID claim is supported;
no promotion is supported.
```

The new M1493 configs extend the active corrected profile directory for the
paper route. Historical M1207/M1212 docs remain historical eight-profile runs;
M1493 is the new evidence artifact for the 12-profile go/no-go matrix config
set.

## Next Route

Admit no-training runtime smoke:

```text
m1494-paper-route-go-no-go-profile-runtime-smoke
```

Candidate command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.controller_profile_runtime_smoke \
  --config-dir configs/paper_route_corrected_profiles \
  --config-glob 'm1207_*.json' \
  --seed 149400 \
  --run-dir runs/m1494_go_no_go_profile_runtime_smoke
```

M1494 must remain no-training/no-PPO/no-promotion infrastructure.

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
