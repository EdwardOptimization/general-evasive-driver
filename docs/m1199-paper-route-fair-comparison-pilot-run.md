# M1199 Paper-Route Fair Comparison Pilot Run

## Summary

M1199 ran the fixed public L0/L1/L2/L3 comparison pilot from M1198.

Decision:

```text
fair_comparison_pilot_completed_route_to_result_audit
```

This is public pilot trend evidence only. It is not a promotion, private
holdout result, paper-level result, recurrent-belief proof, or
self-identification proof.

## Protocol

Artifacts:

```text
runs/m1199_fair_comparison_pilot/summary.json
runs/m1199_fair_comparison_pilot/protocol.json
runs/m1199_fair_comparison_pilot/profile_seed_rows.csv
runs/m1199_fair_comparison_pilot/eval_rows.csv
runs/m1199_fair_comparison_pilot/profile_aggregate.csv
```

Run settings:

```text
main_profiles: L0_current_masked, L1_one_step, L2_window_13, L2_window_25, L2_window_50, L2_window_100, L3_online_gru
diagnostic_profile: L3_reset_control
training_seed_base: 109800
training_seed_offsets: [0, 1, 2]
eval_seed_base: 119800
eval_episodes_per_checkpoint: 64
total_steps_per_seed: 8192
rollout_steps: 128
num_envs: 4
update_epochs: 2
minibatch_size: 256
device: cpu
vector_env_mode: sync
```

The train entrypoint's internal eval was kept to one episode per run. The
comparison eval is the separate masked policy evaluation over public seeds
`119800..119863` for every checkpoint.

## Completion

```text
profile_count: 8
main_profile_count: 7
diagnostic_profile_count: 1
total_seed_runs: 24
completed_seed_runs: 24
failed_seed_runs: 0
main_completed_seed_runs: 21
all_selected_profile_seed_runs_complete: true
all_eval_metrics_finite: true
runtime_seconds: 154.61
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
| `L0_current_masked` | yes | 0.1458 | 0.8333 | 0.1072 | -0.2016 | 27.0871 | 0.8542 |
| `L1_one_step` | yes | 0.2969 | 0.6562 | 0.3505 | -0.1881 | 35.6983 | 0.7031 |
| `L2_window_13` | yes | 0.3854 | 0.4219 | 0.7175 | -0.1580 | 36.6199 | 0.6146 |
| `L2_window_25` | yes | 0.3854 | 0.4219 | 0.7189 | -0.1568 | 36.6392 | 0.6146 |
| `L2_window_50` | yes | 0.3854 | 0.4219 | 0.7189 | -0.1568 | 36.6392 | 0.6146 |
| `L2_window_100` | yes | 0.3854 | 0.4219 | 0.7189 | -0.1568 | 36.6392 | 0.6146 |
| `L3_online_gru` | yes | 0.2552 | 0.7448 | 0.2726 | -0.1865 | 35.4705 | 0.7448 |
| `L3_reset_control` | no | 0.2656 | 0.7135 | 0.2934 | -0.1880 | 36.1018 | 0.7344 |

## Interpretation

Supported public pilot trend:

```text
L2 finite-window profiles are the strongest family in this short fixed-budget pilot.
L1 one-step improves over L0 current-masked.
L3 online-GRU does not beat the L3 reset diagnostic in a way that would support recurrent-hidden benefit.
```

Unsupported claims:

```text
L2 is not promoted.
L2 is not yet a paper-level winner.
L3 is not falsified as an architecture.
GRU recurrent belief is not proven.
Self-identification is not proven.
The pilot does not justify private-holdout evaluation.
```

Two issues need audit before scaling:

```text
1. L2_window_25, L2_window_50, and L2_window_100 are nearly identical, and L2_window_13 is very close.
2. L3_online_gru and L3_reset_control have similar aggregate performance and the same seed-fragility pattern.
```

These may be real short-budget trends, but they may also indicate that the
current finite-window implementation, model capacity, initialization, or task
distribution is not separating temporal profiles strongly enough.

## Failure Taxonomy

```text
failure_types: none
```

No run failed, no metric was non-finite, and no profile-specific tuning or
private holdout was used. The next milestone is still an audit because the
result should not be expanded into a stronger claim without checking the L2
window-equivalence and L3 reset-parity patterns.

## Next Milestone

```text
experiments/manifests/m1200-paper-route-fair-comparison-pilot-result-audit.json
```

M1200 should audit whether the M1199 trends are reliable enough to justify a
longer repeated pilot, or whether the next step should be a finite-window/L3
profile implementation and capacity audit.
