# M1209 Paper-Route Corrected Profile Pilot Run

## Summary

M1209 ran the fixed corrected public L0/L1/L2/L3 profile pilot after M1207
generated corrected configs and M1208 verified their runtime semantics.

Decision:

```text
corrected_profile_pilot_completed_route_to_result_audit
```

This is public pilot trend evidence only. It is not a promotion, private
holdout result, paper-level result, recurrent-belief proof, or
self-identification proof.

## Protocol

Artifacts:

```text
runs/m1209_corrected_profile_pilot/summary.json
runs/m1209_corrected_profile_pilot/protocol.json
runs/m1209_corrected_profile_pilot/profile_seed_rows.csv
runs/m1209_corrected_profile_pilot/eval_rows.csv
runs/m1209_corrected_profile_pilot/profile_aggregate.csv
```

Run settings:

```text
profiles: L0_current_masked, L1_one_step, L2_window_13, L2_window_13_current_tiled, L2_window_25, L2_window_25_current_tiled, L3_online_gru, L3_reset_control_corrected
training_seed_base: 110600
training_seed_offsets: [0, 1, 2]
eval_seed_base: 120600
eval_episodes_per_checkpoint: 64
total_steps_per_seed: 8192
rollout_steps: 128
num_envs: 4
update_epochs: 2
minibatch_size: 256
device: cpu
vector_env_mode: sync
```

The runner writes seeded configs under:

```text
runs/m1209_corrected_profile_pilot/configs
```

and stores each checkpoint under:

```text
runs/m1209_corrected_profile_pilot/profile_runs/<profile>/seed_<seed>/checkpoint.pt
```

## Completion

```text
result_class: corrected_profile_pilot_completed
profile_count: 8
main_profile_count: 5
diagnostic_profile_count: 3
total_seed_runs: 24
completed_seed_runs: 24
failed_seed_runs: 0
all_selected_profile_seed_runs_complete: true
all_eval_metrics_finite: true
runtime_seconds: 121.16
private_holdout_used: false
promoted: false
candidate_replay_started: false
actor_input_contract_changed: false
profile_specific_tuning: false
self_identification_claimed: false
paper_level_claimed: false
```

## Aggregate Public Pilot Metrics

Mean over 3 training seeds, each evaluated on 64 fixed public episodes:

| Profile | Main | Success | Collision | Mean Margin | P10 Margin | Return | Termination |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `L0_current_masked` | yes | 0.1406 | 0.7135 | 0.2349 | -0.1831 | 27.4226 | 0.8594 |
| `L1_one_step` | yes | 0.1406 | 0.7396 | 0.1747 | -0.1905 | 27.2723 | 0.8594 |
| `L2_window_13` | yes | 0.1302 | 0.8073 | 0.0622 | -0.2221 | 29.3339 | 0.8698 |
| `L2_window_13_current_tiled` | no | 0.1094 | 0.8021 | 0.1041 | -0.2009 | 27.0238 | 0.8906 |
| `L2_window_25` | yes | 0.1198 | 0.8177 | 0.0620 | -0.2149 | 28.6718 | 0.8802 |
| `L2_window_25_current_tiled` | no | 0.1146 | 0.7969 | 0.1050 | -0.2024 | 27.2633 | 0.8854 |
| `L3_online_gru` | yes | 0.3594 | 0.5729 | 0.4966 | -0.1278 | 42.9478 | 0.6406 |
| `L3_reset_control_corrected` | no | 0.3594 | 0.5625 | 0.4562 | -0.1478 | 42.9363 | 0.6406 |

## Initial Interpretation

Supported public pilot trends:

```text
L3 online-GRU family is much stronger than L0/L1/L2 in this corrected short public pilot.
L3_online_gru and L3_reset_control_corrected tie on success and termination; online has somewhat better mean/p10 margin, while reset has slightly lower collision.
L2 normal profiles do not beat their current-tiled capacity controls in a way that supports finite-window history necessity.
```

Unsupported claims:

```text
L3 recurrent hidden benefit is not proven.
Finite-window history necessity is not proven.
Self-identification is not proven.
No profile is promoted.
This is not private-holdout or paper-level evidence.
```

The L3 result is encouraging for the online-GRU architecture as a reactive
closed-loop controller, but reset-control parity blocks a recurrent-belief
claim. The L2/current-tiled result is negative for the M1199 finite-window
interpretation and keeps current-frame substitution risk active.

## Runner

M1209 adds:

```text
src/autodrift/corrected_profile_pilot.py
tests/test_corrected_profile_pilot.py
```

The runner:

```text
1. loads committed corrected configs;
2. writes per-profile/per-seed configs;
3. runs train_ppo under the fixed public budget;
4. evaluates each checkpoint through the generated profile runtime mask/reset semantics;
5. writes profile_seed_rows.csv, eval_rows.csv, profile_aggregate.csv, and summary.json.
```

## Verification

Focused runner tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_corrected_profile_pilot.py \
  tests/test_corrected_profile_configs.py \
  tests/test_controller_profile_runtime_smoke.py
```

Result:

```text
16 passed
```

## Next Milestone

```text
experiments/manifests/m1210-paper-route-corrected-profile-pilot-result-audit.json
```

M1210 should audit the M1209 artifacts before any repeat or longer training:

```text
1. validate runner/eval semantics;
2. classify L2 normal-vs-current-tiled as positive, negative, or inconclusive;
3. classify L3 online-vs-corrected-reset as positive, negative, or inconclusive;
4. decide whether the next branch is repeat, architecture repair, longer public pilot, or synthesis.
```
