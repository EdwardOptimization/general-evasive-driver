# M134 Guarded PPO Continuation From S60

M134 tests the first guarded PPO smoke continuation after M133 admitted the M132
s60/anchor20 repair to PPO readiness. The gate is intentionally strict: PPO can
continue only if it preserves M133 behavior retention and strict outcome
proof-surface diversity.

## Configuration

Config: `configs/ppo_m134_guarded_s60_smoke.json`.

Key guards:

- init checkpoint: `runs/m132_margin_retention_s60_anchor20_seed9841/optimized_checkpoint.pt`
- action anchor checkpoint: the same M132 s60 checkpoint
- total steps: `8192`
- rollout steps/envs: `128 x 8`
- learning rate: `1e-6`
- frozen `log_std`
- M128 outcome snippets: `runs/m128_combined_outcome_snippet_corpus/outcome_intervention_snippets.npz`
- actor input: `human_view_online_gru`, `history_length=1`, full previous
  physical commands, zero obstacle relative velocity, no hidden/oracle actor
  fields

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m134_guarded_s60_smoke.json \
  --seed 5134 --device cuda \
  --init-checkpoint runs/m132_margin_retention_s60_anchor20_seed9841/optimized_checkpoint.pt \
  --run-dir runs/ppo_m134_guarded_s60_smoke_seed5134 \
  --eval-episodes 5
```

The checkpoint and action anchor both loaded strictly.

## PPO Smoke

Run directory: `runs/ppo_m134_guarded_s60_smoke_seed5134`.

Built-in eval:

| Return mean | Steps mean | Termination rate | Lateral RMSE | Beta abs error |
| ---: | ---: | ---: | ---: | ---: |
| 87.555162 | 78.6 | 0.0000 | 0.746325 | 0.134741 |

Training metrics show a mechanically valid smoke run, but the last rollout is
not a promotion signal by itself:

| Step | Rollout return | Termination rate | Outcome loss | Anchor loss |
| ---: | ---: | ---: | ---: | ---: |
| 4096 | 72.948060 | 0.133333 | 0.245516 | 0.000166 |
| 8192 | 57.884253 | 0.352941 | 0.257534 | 0.000641 |

## Behavior Gate

Run directory: `runs/m134_guarded_s60_behavior_gate_seed9503`.

| Policy | Success | Termination | Return | Clearance mean | Clearance min |
| --- | ---: | ---: | ---: | ---: | ---: |
| M132 s60 | 0.8625 | 0.1375 | 65.685395 | 1.841558 | -0.144814 |
| M134 step4096 | 0.8625 | 0.1375 | 65.646652 | 1.842102 | -0.142588 |
| M134 final | 0.8625 | 0.1375 | 65.663005 | 1.843000 | -0.140431 |
| M134 final no-action | 0.8625 | 0.1375 | 65.145379 | 1.847037 | -0.130054 |
| M134 final reset | 0.8500 | 0.1500 | 63.780722 | 1.839838 | -0.167922 |
| M134 final zero-current | 0.8000 | 0.2000 | 60.721543 | 1.855723 | -0.143905 |
| M134 final zero-all | 0.8000 | 0.2000 | 60.721543 | 1.855723 | -0.143905 |

Behavior retention passes. The zero-response degradation remains visible and
no-action history remains neutral.

## Fixed-Batch Outcome Loss

Run directory: `runs/m134_outcome_intervention_eval_seed0`.

| Policy | M128 loss mean | Loss std | Loss min | Loss max |
| --- | ---: | ---: | ---: | ---: |
| M132 s60 | 0.252310 | 0.026532 | 0.204511 | 0.297000 |
| M134 step4096 | 0.251846 | 0.026623 | 0.203961 | 0.296615 |
| M134 final | 0.251741 | 0.026755 | 0.203678 | 0.296646 |

The fixed-batch objective improves only slightly. This is not enough to offset
proof-surface regression.

## Strict Proof-Surface Gate

All strict runs use the M133 zero-relvel snapshot-bank relocation settings.
Exact command lines are preserved in each run manifest.

| Policy | Miner seed | Accepted rows | Success-drop pairs | Selected pairs | Selected seeds | Snippets | Max snippet gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M133 M132 s60 | 9900 | 18 | 5 | 10 | 8 | 17 | 0.029413 |
| M133 M132 s60 | 9920 | 15 | 4 | 9 | 8 | 14 | 0.029413 |
| M134 step4096 | 9900 | 17 | 7 | 9 | 6 | 17 | 0.034492 |
| M134 step4096 | 9920 | 17 | 6 | 9 | 7 | 17 | 0.034492 |
| M134 final | 9900 | 17 | 8 | 8 | 5 | 17 | 0.034152 |
| M134 final | 9920 | 17 | 8 | 8 | 6 | 17 | 0.034152 |

M134 preserves behavior and keeps a nonzero proof surface, but it does not
preserve M133 selected diversity. Final PPO falls to `8` selected physical
pairs and `5/6` selected seeds. The `4096` checkpoint is better, but still
below M133 selected-seed diversity.

All accepted snippets remain perturbed-source only.

## Decision

Reject continuation beyond smoke.

M134 proves that the guarded PPO integration is mechanically valid and can
retain behavior, but it does not prove that PPO preserves the self-ID
proof-surface. The next step should be a step-count and anchor-strength
sensitivity gate before any longer PPO continuation.

## Next Step

M135 should test whether smaller PPO steps, stronger action anchoring, or
gate-driven checkpoint selection can preserve M133 strict proof-surface
diversity. If not, PPO should be deferred again in favor of objective-level
or corpus-level repair.
