# M1495 Paper-Route Go/No-Go Profile One-Seed Smoke

## Summary

M1495 runs one fixed-budget train/eval seed for each of the 12 refreshed
go/no-go profile configs.

Decision:

```text
go_no_go_profile_one_seed_smoke_completed_route_to_audit
```

Result class:

```text
corrected_profile_pilot_completed
```

This milestone is plumbing evidence only. It does not promote a checkpoint, use
private holdout, export corpus, change actor inputs, or claim profile ranking,
finite-window history necessity, recurrent belief, or level3 self-ID.

## Command

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

## Completion

Artifact:

```text
runs/m1495_go_no_go_profile_one_seed_smoke/summary.json
```

Completion summary:

```text
result_class: corrected_profile_pilot_completed
profile_count: 12
main_profile_count: 7
diagnostic_profile_count: 5
total_seed_runs: 12
completed_seed_runs: 12
failed_seed_runs: 0
all_selected_profile_seed_runs_complete: true
all_eval_metrics_finite: true
runtime_seconds: 76.0189
private_holdout_used: false
promoted: false
profile_specific_tuning: false
actor_input_contract_changed: false
self_identification_claimed: false
paper_level_claimed: false
```

Protocol:

```text
training_seed_base: 149500
training_seed_offsets: [0]
eval_seed_base: 149600
eval_episodes: 32
device: cpu
```

## Aggregate Metrics

One training seed, evaluated over 32 fixed public episodes:

| Profile | Main | Success | Collision | Mean Margin | P10 Margin | Return |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `L0_current_masked` | yes | 0.1875 | 0.8125 | 0.0321 | -0.2200 | 34.8353 |
| `L1_one_step` | yes | 0.0938 | 0.9062 | -0.0824 | -0.2049 | 28.0408 |
| `L2_window_13` | yes | 0.6875 | 0.3125 | 0.8784 | -0.1210 | 66.6525 |
| `L2_window_13_current_tiled` | no | 0.6875 | 0.3125 | 0.8395 | -0.1231 | 66.5985 |
| `L2_window_25` | yes | 0.6875 | 0.3125 | 0.8825 | -0.1175 | 66.6495 |
| `L2_window_25_current_tiled` | no | 0.6875 | 0.3125 | 0.8397 | -0.1238 | 66.5964 |
| `L2_window_50` | yes | 0.6875 | 0.3125 | 0.8825 | -0.1174 | 66.6495 |
| `L2_window_50_current_tiled` | no | 0.6875 | 0.3125 | 0.8398 | -0.1238 | 66.5964 |
| `L2_window_100` | yes | 0.6875 | 0.3125 | 0.8825 | -0.1174 | 66.6495 |
| `L2_window_100_current_tiled` | no | 0.6875 | 0.3125 | 0.8398 | -0.1238 | 66.5964 |
| `L3_online_gru` | yes | 0.0000 | 1.0000 | -0.1367 | -0.2421 | 22.3274 |
| `L3_reset_control_corrected` | no | 0.1875 | 0.8125 | -0.0034 | -0.2086 | 34.4826 |

## Initial Trend Checks

These are one-seed diagnostics, not conclusions.

L2 normal versus current-tiled:

```text
All L2 windows match their current-tiled controls on success and collision.
Normal L2 has only small mean-margin improvements over current-tiled controls.
```

L3 online versus reset-control:

```text
L3_online_gru success: 0.0000
L3_reset_control_corrected success: 0.1875
```

This is negative for this seed, but M1495 cannot reject L3 because the milestone
is explicitly a one-seed plumbing smoke. M1496 must audit whether to run a
3-seed pilot, repair the L3 training recipe, or route to a different decisive
task before larger training.

## Interpretation

Supported:

```text
The full 12-profile fixed-budget training/eval plumbing completes.
All selected metrics are finite.
The run preserves no-private-holdout, no-promotion, no-profile-specific-tuning,
and no-actor-input-change guardrails.
```

Unsupported:

```text
profile ranking;
finite-window history necessity;
online-GRU hidden advantage;
recurrent self-identification;
promotion;
private holdout generalization.
```

## Next Route

Admit audit:

```text
m1496-paper-route-go-no-go-one-seed-result-audit
```

The audit should decide whether the next step is:

```text
1. a 3-seed public profile pilot;
2. an L3 training-recipe repair/design before another profile pilot;
3. a decisive-task route that does not spend more budget on standard profile
   training.
```

## Guardrails

```text
private_holdout_used: false
promoted: false
profile_specific_tuning: false
actor_input_contract_changed: false
self_identification_claimed: false
paper_level_claimed: false
```
