# M1386 Paper-Route History-Profile One-Seed Fixed-Budget Smoke

## Purpose

M1386 runs the one-seed fixed-budget L0/L1/L2/L3 profile train/eval smoke
admitted by M1385.

This is a plumbing and readiness smoke. It does not promote, use private
holdout, tune profiles, export a corpus, or claim architecture ranking,
paper-level evidence, recurrent-belief advantage, or self-identification.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.corrected_profile_pilot \
  --config-dir configs/paper_route_corrected_profiles \
  --config-glob 'm1207_*.json' \
  --run-dir runs/m1386_history_profile_fixed_budget_smoke \
  --training-seed-base 138600 \
  --seed-offsets 0 \
  --eval-seed-base 138700 \
  --eval-episodes 32 \
  --device cpu
```

## Result

Artifact:

```text
runs/m1386_history_profile_fixed_budget_smoke/summary.json
```

Summary:

```text
result_class: corrected_profile_pilot_completed
profile_count: 8
total_seed_runs: 8
completed_seed_runs: 8
failed_seed_runs: 0
all_selected_profile_seed_runs_complete: true
all_eval_metrics_finite: true
training_seed_base: 138600
training_seed_offsets: [0]
eval_seed_base: 138700
eval_episodes: 32
runtime_seconds: 36.666169955045916
private_holdout_used: false
promoted: false
profile_specific_tuning: false
profile_superiority_claimed: false
self_identification_claimed: false
paper_level_claimed: false
actor_input_contract_changed: false
```

Aggregate public smoke metrics:

| Profile | Success | Collision | Mean Margin | Return | Parameter Count |
| --- | ---: | ---: | ---: | ---: | ---: |
| `L0_current_masked` | 0.62500 | 0.37500 | 1.34657 | 60.34821 | 9095 |
| `L1_one_step` | 0.50000 | 0.50000 | 0.97907 | 53.66424 | 9095 |
| `L2_window_13` | 0.21875 | 0.31250 | 1.39730 | 23.94890 | 29895 |
| `L2_window_13_current_tiled` | 0.21875 | 0.31250 | 1.38395 | 24.28776 | 29895 |
| `L2_window_25` | 0.21875 | 0.31250 | 1.39973 | 23.92489 | 29895 |
| `L2_window_25_current_tiled` | 0.21875 | 0.31250 | 1.38527 | 24.27361 | 29895 |
| `L3_online_gru` | 0.62500 | 0.37500 | 1.19125 | 60.24960 | 42311 |
| `L3_reset_control_corrected` | 0.62500 | 0.37500 | 1.22975 | 60.35347 | 42311 |

## Interpretation

M1386 passes as a one-seed train/eval plumbing smoke:

```text
all eight corrected profiles complete;
all selected metrics are finite;
fixed seed/eval protocol is recorded;
no private holdout, promotion, tuning, or actor-input change occurs.
```

The one-seed trend is not architecture evidence. Still, it is useful to record
before scaling:

```text
L0_current_masked is strong in this seed block.
L1_one_step is weaker than L0 in this seed block.
L2 normal and current-tiled controls are nearly identical by success/collision.
L3 online and corrected reset-control tie by success/collision.
L3 reset has slightly higher mean margin than L3 online in this seed block.
```

This is consistent with the earlier M1213 warning: profile aggregates can be
dominated by current-frame substitution, capacity effects, and seed effects. Do
not scale to a 3-seed public pilot until M1387 audits whether the current
one-seed evidence justifies that cost.

## Decision

Decision:

```text
history_profile_one_seed_smoke_pass_route_to_result_audit
```

Next:

```text
m1387-paper-route-history-profile-one-seed-smoke-result-audit
```

M1387 should decide between:

```text
1. admit a 3-seed public pilot;
2. add a stronger source/history diagnostic before 3-seed training;
3. repair or redesign the profile task if current-frame substitution dominates;
4. stop the fixed-budget refresh branch if it is no longer the highest leverage
   paper-route experiment.
```

## Guardrails

M1386 performs no promotion, private holdout, profile-specific tuning, candidate
replay, source-rich corpus export, actor-input expansion, high-fidelity claim,
paper-level profile-ranking claim, recurrent-belief advantage claim, or level3
self-identification claim.
