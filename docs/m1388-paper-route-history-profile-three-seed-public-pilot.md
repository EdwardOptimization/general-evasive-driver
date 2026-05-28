# M1388 Paper-Route History-Profile Three-Seed Public Pilot

## Purpose

M1388 runs the three-seed fixed-budget public L0/L1/L2/L3 profile pilot admitted
by M1387.

This is public trend evidence only. It does not promote, use private holdout,
tune profiles, export a corpus, claim paper-level evidence, claim architecture
ranking, claim recurrent-belief advantage, or claim self-identification.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.corrected_profile_pilot \
  --config-dir configs/paper_route_corrected_profiles \
  --config-glob 'm1207_*.json' \
  --run-dir runs/m1388_history_profile_three_seed_public_pilot \
  --training-seed-base 138800 \
  --seed-offsets 0,1,2 \
  --eval-seed-base 138900 \
  --eval-episodes 64 \
  --device cpu
```

## Result

Artifact:

```text
runs/m1388_history_profile_three_seed_public_pilot/summary.json
```

Summary:

```text
result_class: corrected_profile_pilot_completed
profile_count: 8
total_seed_runs: 24
completed_seed_runs: 24
failed_seed_runs: 0
all_selected_profile_seed_runs_complete: true
all_eval_metrics_finite: true
training_seed_base: 138800
training_seed_offsets: [0, 1, 2]
eval_seed_base: 138900
eval_episodes: 64
runtime_seconds: 119.38639532809611
private_holdout_used: false
promoted: false
profile_specific_tuning: false
profile_superiority_claimed: false
self_identification_claimed: false
paper_level_claimed: false
actor_input_contract_changed: false
```

Aggregate public pilot metrics:

| Profile | Success | Collision | Mean Margin | Return | Parameter Count |
| --- | ---: | ---: | ---: | ---: | ---: |
| `L0_current_masked` | 0.52083 | 0.38542 | 0.78989 | 49.63706 | 9095 |
| `L1_one_step` | 0.47396 | 0.43229 | 0.67413 | 47.17097 | 9095 |
| `L2_window_13` | 0.56771 | 0.43229 | 0.71303 | 55.97211 | 29895 |
| `L2_window_13_current_tiled` | 0.56250 | 0.43750 | 0.70532 | 55.66599 | 29895 |
| `L2_window_25` | 0.55729 | 0.44271 | 0.70168 | 55.38998 | 29895 |
| `L2_window_25_current_tiled` | 0.56250 | 0.43750 | 0.70587 | 55.69459 | 29895 |
| `L3_online_gru` | 0.44271 | 0.54688 | 0.49734 | 45.97498 | 42311 |
| `L3_reset_control_corrected` | 0.46354 | 0.52604 | 0.51299 | 46.85772 | 42311 |

## Public Trend Interpretation

M1388 passes as a completed public pilot:

```text
24 / 24 profile seed runs complete;
all selected metrics finite;
fixed profile/eval protocol recorded;
no private holdout, promotion, tuning, actor-input change, paper-level claim, or
self-ID claim.
```

Trend classifications to audit in M1389:

```text
L2 family strongest by success among trained profiles.
L2 normal does not meaningfully beat current-tiled controls.
L3 online GRU is weaker than corrected reset-control in aggregate.
L3 online GRU is weaker than L0 and L2 families in this public pilot.
Current-frame substitution and temporal-GRU capacity remain active explanations.
```

This does not prove L3 is bad. It says this fixed-budget public profile pilot is
not positive evidence for online recurrent hidden-state utility.

## Decision

Decision:

```text
history_profile_three_seed_public_pilot_complete_route_to_result_audit
```

Next:

```text
m1389-paper-route-history-profile-three-seed-public-pilot-result-audit
```

M1389 should decide whether to:

```text
1. stop profile scaling and move to stronger causal history-necessity tasks;
2. redesign task/curriculum so history is actually required;
3. run a targeted L3 repair branch;
4. or, only with a specific reason, run another profile repeat.
```

## Guardrails

M1388 performs no promotion, private holdout, profile-specific tuning, candidate
replay, source-rich corpus export, actor-input expansion, high-fidelity claim,
paper-level profile-ranking claim, recurrent-belief advantage claim, or level3
self-identification claim.
