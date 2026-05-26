# M972 V4 Public Base Post-Promotion Guarded PPO Smoke Implementation

## Purpose

M972 runs the first smoke-scale guarded PPO proposal from the promoted alpha
`1.0` public-gate base.

Base checkpoint:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

Raw PPO checkpoint:

```text
runs/ppo_m972_post_promotion_guarded_smoke_seed5972/checkpoint.pt
```

M972 does not promote, use private holdout, change actor inputs, or make a
long-PPO capability claim.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_post_promotion_guarded_ppo_smoke
```

The wrapper launches:

```bash
python -m autodrift.train_ppo \
  --config configs/ppo_m972_post_promotion_guarded_smoke.json \
  --init-checkpoint runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt \
  --run-dir runs/ppo_m972_post_promotion_guarded_smoke_seed5972 \
  --device auto
```

## Result

```text
result_class: post_promotion_guarded_ppo_proof_washout
ppo_returncode: 0
training_metrics_finite: true
actor_inputs_changed: false
proof_pass: false
generalization_pass: true
behavior_pass: true
promoted: false
private_holdout_used: false
```

The PPO proposal ran successfully and produced a checkpoint. The failure is not
training instability, broad generalization regression, behavior regression, or
actor-contract drift. It is a proof retention failure.

## PPO Smoke Output

The PPO subprocess completed one `1024` step update:

```text
training_device: cuda
num_envs: 8
rollout_return_mean: 83.12
reward_mean: 1.137
episode_count: 11
eval_return_mean: 69.64235273838354
eval_steps_mean: 76.2
eval_termination_rate: 0.2
```

Training-time metrics are finite, but they are not a promotion signal.

## Proof Gates

M972 compares the raw PPO checkpoint against alpha `1.0` on the six public
replay surfaces.

| Surface | Base success-drop | Candidate success-drop | Gate |
| --- | ---: | ---: | --- |
| M183/M168 | 16 | 16 | pass |
| M183/M170 | 17 | 17 | pass |
| M193/M189 | 14 | 14 | pass |
| M212/M204 | 17 | 17 | pass |
| M223/M219 | 17 | 17 | pass |
| M267/M264 | 17 | 15 | fail |

M267/M264 is the only failed surface. Normal-history success and normal margin
retention pass there:

```text
candidate_normal_success_rate: 1.0
normal_success_delta: 0.0
normal_margin_mean_delta: +0.00027326016175324534
```

The failure is that wrong-history rollouts became safe on two rows:

| Row | Target | Pair | Base wrong margin | M972 wrong margin | M972 wrong success |
| ---: | --- | --- | ---: | ---: | --- |
| 6 | future_braking_deceleration | 9530:15:9550:18 | -0.00011365403926677509 | 0.00001979621605041615 | true |
| 15 | future_braking_deceleration | 9530:21:9550:21 | -0.00004219117477299861 | 0.0002458431812417672 | true |

This is the same failure shape the readiness gate was meant to catch: the raw
PPO step keeps broad behavior and normal branch safety while weakening the
wrong-history counterfactual proof.

## Fresh Generalization

Fresh public and moderate OOD comparisons all pass.

| Distribution | Seed | Base success | Candidate success | Margin delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| fresh_public | 96700 | 0.83984375 | 0.83984375 | +0.00010482379112941587 | true |
| fresh_public | 96701 | 0.83984375 | 0.83984375 | +0.00010556001064010445 | true |
| moderate_ood | 96720 | 0.625 | 0.625 | +0.000256893515000467 | true |

These results are useful diagnostics, but they cannot override the proof
washout.

## Behavior And Ablation Gates

Behavior seeds retain baseline success and reset/zero-all ordering.

| Seed | Base success | Candidate success | Reset success | Zero-all success | Pass |
| ---: | ---: | ---: | ---: | ---: | --- |
| 9505 | 0.8625 | 0.8625 | 0.85 | 0.8 | true |
| 9506 | 0.8625 | 0.8625 | 0.85 | 0.8 | true |
| 96730 | 0.8375 | 0.8375 | 0.825 | 0.825 | true |
| 96731 | 0.8375 | 0.8375 | 0.825 | 0.825 | true |

This supports the narrow diagnosis: M972 does not broadly damage the current
driver behavior, but it is not proof-retaining.

## Decision

M972 rejects the raw PPO checkpoint for promotion.

The route is:

```text
post-promotion guarded PPO exact repair/projection design
```

The next milestone should not lengthen PPO or increase scalar auxiliary
pressure blindly. It should first design an exact post-PPO repair/projection
step that treats PPO as a proposal and restores full-corpus proof feasibility
before replay or promotion.

## Artifacts

```text
runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/summary.json
runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/ppo_run_dir.txt
runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/proof_replay_summary.csv
runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/generalization_comparison.csv
runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/behavior_comparison.csv
runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/route_decision.csv
```

## Next Blocker

```text
m973-v4-public-base-post-promotion-ppo-exact-repair-projection-design
```

M973 should design the exact repair/projection milestone before any further
PPO continuation.
