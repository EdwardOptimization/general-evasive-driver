# M156 Capability-Belief Critical-Key Safe Repair

M155 showed that an 80-step capability-belief auxiliary update improves fixed
validation losses but breaks the protected rollout key
`9944|perturbed|28|28`. M156 tests the smallest repair: keep the same M151
capability-belief objective and M142 initialization, but reduce the auxiliary
update to 20 steps before repeating the cheap M154 prescreens.

This is an objective-sanity repair, not a driver promotion.

## Candidate

Run:

```text
runs/m156_capability_belief_aux_s20_seed9630
```

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.capability_belief_aux_candidate \
  --init-checkpoint runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt \
  --dataset-npz runs/m151_capability_belief_dataset_multiseed/capability_belief_dataset.npz \
  --optimization-seeds 9630 \
  --train-fraction 0.70 \
  --steps 20 \
  --batch-size 64 \
  --learning-rate 0.0001 \
  --weight-decay 0.001 \
  --history-window 25 \
  --feature-source response_hidden \
  --delta-loss-coef 0.5 \
  --anchor-coef 10.0 \
  --device cpu \
  --run-dir runs/m156_capability_belief_aux_s20_seed9630
```

Actor contract:

```text
actor_encoder: human_view_online_gru
actor_obs_dim: 72
hidden diagnostics as actor inputs: no
```

Validation improvements, before minus after:

| Metric | Improvement |
| --- | ---: |
| combined loss | 0.108913 |
| target loss | 0.068497 |
| pairwise delta loss | 0.080831 |
| feature anchor loss after | 0.000407 |

Per-target validation improvements:

| Target | Target loss improvement | Delta loss improvement |
| --- | ---: | ---: |
| future braking deceleration | 0.047941 | 0.031874 |
| future yaw response | 0.108458 | 0.175753 |
| future lateral acceleration response | 0.049093 | 0.034866 |

The repair is deliberately weaker than M155. M155 had larger loss improvement
but failed rollout-key safety. M156 keeps a smaller positive objective signal
with a much smaller feature anchor drift.

## Protected Critical Key

Run:

```text
runs/m156_critical_key_prescreen_s20_seed9944
```

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.critical_key_replay_guard \
  --reference-manifest runs/m133_zero_relvel_s60_strict_60ep_seed9900/manifest.json \
  --reference-cases-csv runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv \
  --reference-cases-csv runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv \
  --case-key '9944|perturbed|28|28' \
  --checkpoint-policy m142_a400=runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt \
  --checkpoint-policy m156_s20=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --reference-policy m142_a400 \
  --device cpu \
  --run-dir runs/m156_critical_key_prescreen_s20_seed9944
```

Result:

| Policy | Accepted cases | Protected margin gap | Pass |
| --- | ---: | ---: | --- |
| m142_a400 | 1 / 1 | 0.005014 | true |
| m156_s20 | 1 / 1 | 0.009455 | true |

`guard_validated` is `false` in this run only because no non-reference policy
failed. The relevant candidate evidence is `m156_s20 policy_pass=True`.

## Behavior Prescreens

Runs:

```text
runs/m156_behavior_prescreen_s20_seed9503
runs/m156_behavior_prescreen_s20_seed9504
```

Commands are the M154 cheap behavior prescreen with M142, M156, and M156
response-history ablations:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.benchmark \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --episodes 80 \
  --seed <9503-or-9504> \
  --policies heuristic \
  --checkpoint-policy m142_a400=runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt \
  --checkpoint-policy m156_s20=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --checkpoint-policy m156_s20_reset=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m156_s20_zero_current=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt@zero_current_response \
  --checkpoint-policy m156_s20_zero_all=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt@zero_all_response \
  --checkpoint-policy m156_s20_noact=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt@zero_action_history \
  --device cpu \
  --run-dir runs/m156_behavior_prescreen_s20_seed<9503-or-9504>
```

Seed 9503:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m142_a400 | 0.8625 | 0.1375 | 1.841495 |
| m156_s20 | 0.8625 | 0.1375 | 1.845927 |
| m156_s20_reset | 0.8500 | 0.1250 | 1.841019 |
| m156_s20_zero_current | 0.8000 | 0.1250 | 1.856803 |
| m156_s20_zero_all | 0.8000 | 0.1250 | 1.856803 |
| m156_s20_noact | 0.8625 | 0.1375 | 1.848034 |

Seed 9504:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m142_a400 | 0.8625 | 0.1375 | 1.849323 |
| m156_s20 | 0.8625 | 0.1375 | 1.853662 |
| m156_s20_reset | 0.8500 | 0.1250 | 1.849124 |
| m156_s20_zero_current | 0.8000 | 0.1250 | 1.868621 |
| m156_s20_zero_all | 0.8000 | 0.1250 | 1.868621 |
| m156_s20_noact | 0.8625 | 0.1375 | 1.857173 |

The candidate matches M142 aggregate success on both behavior seeds. The
zero-current and zero-all response interventions still reduce success to
`0.8000`, so the old response-history dependence signal is retained.

## Decision

M156 is a positive key-safe repair smoke.

It does not prove driver-like self-identification. It only shows that a smaller
capability-belief update can keep a positive M151 objective signal while passing
the protected critical-key replay and cheap behavior prescreens.

Decision: admit `runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt`
to a full M154 gate repeat. Do not start PPO until that repeat passes.
