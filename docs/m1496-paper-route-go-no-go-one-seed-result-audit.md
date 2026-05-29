# M1496 Paper-Route Go/No-Go One-Seed Result Audit

## Summary

M1496 audits the M1495 one-seed fixed-budget go/no-go profile smoke before any
3-seed public pilot.

Decision:

```text
go_no_go_one_seed_audit_clean_plumbing_admit_three_seed_public_pilot
```

This audit does not train, run PPO, run replay, promote, use private holdout,
export corpus, change actor inputs, or claim profile ranking or self-ID.

## Completion Audit

M1495 completed the plumbing objective:

```text
profile_count: 12
main_profile_count: 7
diagnostic_profile_count: 5
total_seed_runs: 12
completed_seed_runs: 12
failed_seed_runs: 0
all_selected_profile_seed_runs_complete: true
all_eval_metrics_finite: true
private_holdout_used: false
promoted: false
profile_specific_tuning: false
actor_input_contract_changed: false
self_identification_claimed: false
paper_level_claimed: false
```

So M1495 is a valid one-seed plumbing pass.

## One-Seed Trend Audit

The one-seed trend is informative but not conclusive.

L2 normal/current-tiled:

```text
L2_window_13 success/collision:              0.6875 / 0.3125
L2_window_13_current_tiled:                  0.6875 / 0.3125
L2_window_25:                                0.6875 / 0.3125
L2_window_25_current_tiled:                  0.6875 / 0.3125
L2_window_50:                                0.6875 / 0.3125
L2_window_50_current_tiled:                  0.6875 / 0.3125
L2_window_100:                               0.6875 / 0.3125
L2_window_100_current_tiled:                 0.6875 / 0.3125
```

The normal L2 windows have slightly higher mean margins, but current-tiled
controls match success and collision exactly in this seed. This is consistent
with earlier M1388/M1389 negative evidence for finite-window history necessity
on the standard distribution.

L3 online/reset:

```text
L3_online_gru success/collision/margin:          0.0000 / 1.0000 / -0.1367
L3_reset_control_corrected success/collision:    0.1875 / 0.8125
```

This one seed is negative for online-GRU hidden benefit. It also matches the
earlier warning that standard fixed-budget public profile training may not be
the right distribution or recipe for proving recurrent self-ID.

## Classification

M1496 classifies M1495 as:

```text
plumbing_completion: pass
profile_ranking_evidence: not_allowed
finite_window_history_necessity: not_supported_by_one_seed
online_gru_hidden_advantage: not_supported_by_one_seed
current_frame_substitution_risk: high
three_seed_public_pilot_admission: allowed_with_stop_rule
```

The reason to admit a 3-seed public pilot is not optimism about L3. It is to
produce a complete full-12-profile public matrix baseline after M1493/M1494
fixed the config/runtime layer. That baseline is needed for the paper route
even if it returns a negative verdict for recurrent history on the standard
distribution.

## Three-Seed Stop Rule

M1497 may run exactly one 3-seed public pilot.

If M1497 repeats both patterns:

```text
1. L2 current-tiled controls remain close to L2 normal;
2. L3 online does not beat corrected reset-control;
```

then M1498 must stop standard profile-scaling and route to one of:

```text
decisive T4/T5 task evidence;
L3 training-recipe repair;
or a negative/conditional profile verdict for the standard distribution.
```

Do not keep scaling profile pilots after a repeated negative trend.

## Next Route

Admit:

```text
m1497-paper-route-go-no-go-profile-three-seed-public-pilot
```

Candidate command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.corrected_profile_pilot \
  --config-dir configs/paper_route_corrected_profiles \
  --config-glob 'm1207_*.json' \
  --run-dir runs/m1497_go_no_go_profile_three_seed_public_pilot \
  --training-seed-base 149700 \
  --seed-offsets 0,1,2 \
  --eval-seed-base 149800 \
  --eval-episodes 64 \
  --device cpu
```

M1497 is public trend evidence only and must route to M1498 audit before any
private holdout, promotion, or profile-ranking claim.

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
