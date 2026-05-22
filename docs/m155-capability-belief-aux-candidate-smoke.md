# M155 Capability-Belief Aux Candidate Smoke

M155 creates a small capability-belief auxiliary candidate from the guarded
M142 baseline, then runs the cheapest parts of the M154 behavior gate before
any strict miner or PPO promotion.

This is a candidate smoke, not a driver promotion. The actor observation
contract remains the canonical 72-value P0 human-view input:

```text
actor_encoder: human_view_online_gru
actor_obs_dim: 72
hidden physics / diagnostics as actor inputs: no
```

## Candidate

New harness:

```text
src/autodrift/capability_belief_aux_candidate.py
tests/test_capability_belief_aux_candidate.py
```

Run:

```text
runs/m155_capability_belief_aux_candidate_seed9620
```

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.capability_belief_aux_candidate \
  --init-checkpoint runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt \
  --dataset-npz runs/m151_capability_belief_dataset_multiseed/capability_belief_dataset.npz \
  --optimization-seeds 9620 \
  --train-fraction 0.70 \
  --steps 80 \
  --batch-size 64 \
  --learning-rate 0.0001 \
  --weight-decay 0.001 \
  --history-window 25 \
  --feature-source response_hidden \
  --delta-loss-coef 0.5 \
  --anchor-coef 10.0 \
  --device cpu \
  --run-dir runs/m155_capability_belief_aux_candidate_seed9620
```

Artifacts:

```text
runs/m155_capability_belief_aux_candidate_seed9620/optimized_checkpoint.pt
runs/m155_capability_belief_aux_candidate_seed9620/summary.json
runs/m155_capability_belief_aux_candidate_seed9620/loss_summary.csv
runs/m155_capability_belief_aux_candidate_seed9620/seed_summary.csv
```

Validation improvements, before minus after:

| Metric | Improvement |
| --- | ---: |
| validation combined loss | 0.548986 |
| validation target loss | 0.250640 |
| validation pairwise delta loss | 0.596691 |
| validation feature anchor loss after | 0.008260 |

Per-target validation improvements:

| Target | Target loss improvement | Delta loss improvement |
| --- | ---: | ---: |
| future braking deceleration | 0.188389 | 0.310920 |
| future yaw response | 0.365003 | 1.095529 |
| future lateral acceleration response | 0.198530 | 0.383623 |

The fixed capability objective passes. This only proves that the auxiliary
target can be optimized from P0 response history with a small feature anchor.

## Cheap Behavior Prescreen

Run:

```text
runs/m155_capability_belief_behavior_prescreen_seed9503
```

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.benchmark \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --episodes 80 \
  --seed 9503 \
  --policies heuristic \
  --checkpoint-policy m142_a400=runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt \
  --checkpoint-policy m155_candidate=runs/m155_capability_belief_aux_candidate_seed9620/optimized_checkpoint.pt \
  --checkpoint-policy m155_candidate_reset=runs/m155_capability_belief_aux_candidate_seed9620/optimized_checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m155_candidate_zero_current=runs/m155_capability_belief_aux_candidate_seed9620/optimized_checkpoint.pt@zero_current_response \
  --checkpoint-policy m155_candidate_zero_all=runs/m155_capability_belief_aux_candidate_seed9620/optimized_checkpoint.pt@zero_all_response \
  --checkpoint-policy m155_candidate_noact=runs/m155_capability_belief_aux_candidate_seed9620/optimized_checkpoint.pt@zero_action_history \
  --device cpu \
  --run-dir runs/m155_capability_belief_behavior_prescreen_seed9503
```

Key results:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m142_a400 | 0.8625 | 0.1375 | 1.841495 |
| m155_candidate | 0.8625 | 0.1375 | 1.823737 |
| m155_candidate_reset | 0.8500 | 0.1250 | 1.832171 |
| m155_candidate_zero_current | 0.8000 | 0.1250 | 1.854834 |
| m155_candidate_zero_all | 0.8000 | 0.1250 | 1.854834 |
| m155_candidate_noact | 0.8625 | 0.1375 | 1.837875 |

The cheap behavior seed does not show an aggregate success regression versus
M142. Zero-current and zero-all response interventions reduce success to
`0.8000`, so the candidate still has a visible response-chain dependence on
this prescreen.

## Critical-Key Replay

Run:

```text
runs/m155_capability_belief_critical_key_prescreen_seed9944
```

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.critical_key_replay_guard \
  --reference-manifest runs/m133_zero_relvel_s60_strict_60ep_seed9900/manifest.json \
  --reference-cases-csv runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv \
  --reference-cases-csv runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv \
  --case-key '9944|perturbed|28|28' \
  --checkpoint-policy m142_a400=runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt \
  --checkpoint-policy m155_candidate=runs/m155_capability_belief_aux_candidate_seed9620/optimized_checkpoint.pt \
  --reference-policy m142_a400 \
  --device cpu \
  --run-dir runs/m155_capability_belief_critical_key_prescreen_seed9944
```

Result:

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m142_a400 | 1 / 1 | true |
| m155_candidate | 0 / 1 | false |

The protected key is `9944|perturbed|28|28`. M142 reproduces it with margin gap
`0.005014`, but M155 candidate drops the same key to `0.002813`, below the
strict accepted threshold. This is the same near-threshold surface that M140 and
M141 identified as a cheap rollout-safety guard.

## Decision

M155 is rejected for M154 gate admission.

The important result is not that the auxiliary objective is useless. It is that
a small anchored capability-belief update can improve fixed validation losses
and preserve aggregate behavior while still breaking a rollout-critical proof
surface. This repeats the M137/M139 lesson: fixed losses and small feature/action
anchors are not enough to guarantee rollout-key survival.

Next step: repair the capability-belief update with a key-safe or
rollout-margin-aware anchor before running strict miners or PPO.
