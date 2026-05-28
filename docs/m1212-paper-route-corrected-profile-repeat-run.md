# M1212 Paper-Route Corrected Profile Repeat Run

## Summary

M1212 ran the fresh public corrected profile repeat designed in M1211.

Decision:

```text
corrected_profile_repeat_completed_route_to_repeat_result_audit
```

This is public repeat trend evidence only. It is not a promotion, private
holdout result, paper-level result, recurrent-belief proof, or
self-identification proof.

## Protocol

Artifacts:

```text
runs/m1212_corrected_profile_repeat/summary.json
runs/m1212_corrected_profile_repeat/protocol.json
runs/m1212_corrected_profile_repeat/profile_seed_rows.csv
runs/m1212_corrected_profile_repeat/eval_rows.csv
runs/m1212_corrected_profile_repeat/profile_aggregate.csv
```

Run settings:

```text
profiles: same eight M1207 corrected profiles
training_seed_base: 111600
training_seed_offsets: [0, 1, 2]
eval_seed_base: 121600
eval_episodes_per_checkpoint: 64
total_steps_per_seed: 8192
rollout_steps: 128
num_envs: 4
update_epochs: 2
minibatch_size: 256
device: cpu
vector_env_mode: sync
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
runtime_seconds: 120.63
private_holdout_used: false
promoted: false
candidate_replay_started: false
actor_input_contract_changed: false
profile_specific_tuning: false
self_identification_claimed: false
paper_level_claimed: false
```

## Aggregate Public Repeat Metrics

Mean over 3 training seeds, each evaluated on 64 fixed public episodes:

| Profile | Main | Success | Collision | Mean Margin | P10 Margin | Return | Termination |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `L0_current_masked` | yes | 0.2240 | 0.6250 | 0.3540 | -0.1864 | 30.2951 | 0.7760 |
| `L1_one_step` | yes | 0.3385 | 0.5156 | 0.4758 | -0.1736 | 36.3675 | 0.6615 |
| `L2_window_13` | yes | 0.4062 | 0.4792 | 0.5237 | -0.1426 | 41.9741 | 0.5938 |
| `L2_window_13_current_tiled` | no | 0.4271 | 0.4427 | 0.6153 | -0.1342 | 42.3426 | 0.5729 |
| `L2_window_25` | yes | 0.4115 | 0.4740 | 0.5240 | -0.1382 | 42.2372 | 0.5885 |
| `L2_window_25_current_tiled` | no | 0.4271 | 0.4427 | 0.6191 | -0.1407 | 42.3109 | 0.5729 |
| `L3_online_gru` | yes | 0.1875 | 0.8073 | 0.1225 | -0.2106 | 32.8460 | 0.8125 |
| `L3_reset_control_corrected` | no | 0.1354 | 0.8646 | 0.0651 | -0.2250 | 29.7287 | 0.8646 |

## Pre-Registered Pair Checks

L2 normal minus current-tiled:

| Pair | Success Delta | Collision Delta | Mean Margin Delta | P10 Margin Delta | Return Delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| `L2_window_13 - current_tiled` | -0.0208 | +0.0365 | -0.0916 | -0.0084 | -0.3684 |
| `L2_window_25 - current_tiled` | -0.0156 | +0.0312 | -0.0951 | +0.0025 | -0.0738 |

Classification under M1211 thresholds:

```text
negative_for_finite_window_history_necessity
```

L3 online minus corrected reset-control:

| Pair | Success Delta | Collision Delta | Mean Margin Delta | P10 Margin Delta | Return Delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| `L3_online_gru - L3_reset_control_corrected` | +0.0521 | -0.0573 | +0.0574 | +0.0144 | +3.1173 |

Classification under M1211 thresholds:

```text
aggregate_positive_for_online_vs_reset
not_yet_recurrent_hidden_or_self_id_evidence
```

Online beats corrected reset in aggregate, but the whole L3 family is much
weaker than L2/current-tiled in this seed block. This conflicts with M1209's
L3-family-winner trend and needs a cross-block audit.

## Initial Interpretation

Supported:

```text
M1212 completed a valid fresh public repeat.
L2 current-tiled controls again block finite-window history-necessity claims.
L3 online is better than corrected reset in this repeat, but L3 family ranking is unstable across seed blocks.
```

Unsupported:

```text
stable profile ranking
finite-window history necessity
GRU recurrent-hidden benefit as a paper-level claim
self-identification
promotion
private-holdout generalization
```

## Next Milestone

```text
experiments/manifests/m1213-paper-route-corrected-profile-repeat-result-audit.json
```

M1213 should compare M1209 and M1212 before deciding whether to synthesize,
repeat again, repair profiles/tasks, or move to stronger causal history gates.
