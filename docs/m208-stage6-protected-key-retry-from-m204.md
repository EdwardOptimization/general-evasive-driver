# M208 Stage6 Protected-Key Retry From M204

M208 ran the one allowed fresh-seed stage6 retry from M204 after M206 failed
the protected-key boundary-window guard.

This milestone uses the frozen M196 guarded PPO smoke config and does not change
actor inputs.

## Pre-Registered Rule

M207 allowed exactly one retry from the retained M204 checkpoint:

```text
runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt
```

If this retry also fails protected key `9944|perturbed|28|28`, the same PPO
recipe must stop. The next step must be a protected-key-aware objective or
config design, not another retry seed.

## Training

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m196_guarded_from_m194_smoke.json \
  --seed 5213 \
  --init-checkpoint runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt \
  --run-dir runs/ppo_m208_stage6_retry_from_m204_seed5213
```

Artifacts:

- `runs/ppo_m208_stage6_retry_from_m204_seed5213/checkpoint.pt`
- `runs/ppo_m208_stage6_retry_from_m204_seed5213/train_metrics.csv`
- `runs/ppo_m208_stage6_retry_from_m204_seed5213/eval_summary.json`

Final train metrics:

| Metric | Value |
| --- | ---: |
| rollout_return_mean | 70.415314 |
| reward_mean | 1.059848 |
| episode_count | 11 |
| train termination_rate | 0.181818 |
| outcome_loss | 0.161092 |
| anchor_loss | 0.000453 |

Smoke eval:

| Metric | Value |
| --- | ---: |
| return_mean | 77.466617 |
| steps_mean | 66.400000 |
| termination_rate | 0.000000 |
| lateral_rmse_mean | 0.632384 |
| beta_abs_error_mean | 0.158989 |

## Fixed M193 Objective

Artifact:

```text
runs/m208_fixed_batch_outcome_eval_seed37/summary.json
```

| Policy | Fixed loss mean |
| --- | ---: |
| m204_stage5 | 0.158474873 |
| m206_stage6 | 0.158420356 |
| m208_retry | 0.158354129 |

M208 improves the fixed M193 objective beyond M206. This is not sufficient for
promotion because protected-key retention is a hard gate.

## Replay Gates

All broad replay-retention gates pass against the M204 baseline.

| Gate | Rows | Candidate drops | Gate pass | Normal margin delta | Margin gap delta |
| --- | ---: | ---: | --- | ---: | ---: |
| M183 M168 | 16 | 16 / 16 | true | 0.000406 | 0.000094 |
| M183 M170 | 17 | 17 / 17 | true | 0.000401 | 0.000094 |
| M193 M189 | 14 | 14 / 14 | true | 0.000370 | 0.000181 |

Artifacts:

- `runs/m208_m183_m168_replay_gate_seed9510/summary.json`
- `runs/m208_m183_m170_replay_gate_seed9510/summary.json`
- `runs/m208_m193_m189_replay_gate_seed9630/summary.json`

## Behavior Gates

Artifacts:

- `runs/m208_behavior_gate_seed9505/policy_summary.csv`
- `runs/m208_behavior_gate_seed9506/policy_summary.csv`

| Seed | Policy | Success | Mean clearance margin |
| --- | --- | ---: | ---: |
| 9505 | m204_stage5 | 0.8625 | 1.836804 |
| 9505 | m206_stage6 | 0.8625 | 1.836698 |
| 9505 | m208_retry | 0.8625 | 1.836938 |
| 9505 | m208_retry_reset | 0.8500 | 1.834812 |
| 9505 | m208_retry_zero_all | 0.8000 | 1.852125 |
| 9506 | m204_stage5 | 0.8625 | 1.854415 |
| 9506 | m206_stage6 | 0.8625 | 1.854295 |
| 9506 | m208_retry | 0.8625 | 1.854545 |
| 9506 | m208_retry_reset | 0.8500 | 1.851106 |
| 9506 | m208_retry_zero_all | 0.8000 | 1.870104 |

Normal behavior is retained on both seeds, and reset/zero-all degradation is
still present.

## Protected Key

Artifact:

```text
runs/m208_critical_key_seed9944/guard_results.csv
```

Protected key:

```text
9944|perturbed|28|28
```

| Policy | Accepted cases | Normal success | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m199_5201 | 1 / 1 | true | 0.119416 | 0.068219 | 0.051197 |
| m204_stage5 | 1 / 1 | true | 0.189607 | 0.094102 | 0.095505 |
| m206_stage6 | 0 / 1 | true | 0.207450 | 0.109548 | 0.097903 |
| m208_retry | 0 / 1 | true | 0.208742 | 0.111262 | 0.097479 |

M208 repeats the M206 failure mechanism: the selected key remains normally
successful and keeps a large wrong-history margin gap, but its normal margin is
outside the pre-registered near-boundary window:

```text
M208 normal margin = 0.208742
reference max_normal_margin = 0.2
```

The second candidate row in
`runs/m208_critical_key_seed9944/m208_retry_candidates.csv` confirms
`perturbed_margin_gap_accept=True` and
`perturbed_accepted_outcome_sensitive=False`.

## Decision

Reject M208 as a promotable stage6 checkpoint.

M208 is positive on fixed objective, broad replay gates, and broad behavior, but
fails the hard protected-key retention gate. Because M206 and M208 both fail
the same protected key through the same boundary-window excursion, the failure
is no longer treated as a single-seed accident.

Current best retained checkpoint remains:

```text
runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt
```

Decision:

```text
reject_stage6_retry_protected_key_failure
```

Next step:

```text
m209-protected-key-aware-stage6-design
```

M209 must design a protected-key-aware objective or config before any further
PPO. It must not run another same-recipe stage6 retry.
