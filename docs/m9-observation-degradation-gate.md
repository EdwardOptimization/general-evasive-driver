# M9 Observation-Degradation Gate

Last updated: 2026-05-21

## Purpose

M8 still did not degrade under no-action-history, shuffled-history, or
single-frame-history ablations. M9 adds response-feature ablations to test
whether the current obstacle benchmark is being solved by single-frame
shortcuts rather than professional-driver-like closed-loop identification.

The new checkpoint ablations are:

- `zero_current_response`: zero current-frame `vx`, `vy`, yaw rate, sideslip,
  steering state, drive/brake state, and action-history features while leaving
  older history frames intact.
- `zero_all_response`: zero the same response features in every history frame.

If the task truly requires response-history inference, `zero_current_response`
should preserve some performance while `zero_all_response`,
`single_frame_history`, or `shuffled_history` should lose performance.

## Command

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/m8_history_critical_obstacle_holdout_eval.json \
  --episodes 40 \
  --seed 1600 \
  --policies envelope_aes \
  --checkpoint-policy m8=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt \
  --checkpoint-policy m8_zero_current=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt@zero_current_response \
  --checkpoint-policy m8_zero_all=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt@zero_all_response \
  --checkpoint-policy m8_single=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt@single_frame_history \
  --checkpoint-policy m8_shuffle=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt@shuffled_history \
  --device cpu \
  --run-dir runs/research_m9_observation_degradation_gate
```

## Result

| policy | success | collision | high sideslip | return |
| --- | ---: | ---: | ---: | ---: |
| envelope AES | 0.225 | 0.775 | 0.000 | 6.662 |
| M8 | 0.275 | 0.725 | 0.009 | 10.754 |
| M8 zero current response | 0.275 | 0.725 | 0.010 | 10.796 |
| M8 zero all response | 0.275 | 0.725 | 0.007 | 10.844 |
| M8 single-frame history | 0.275 | 0.725 | 0.010 | 10.826 |
| M8 shuffled history | 0.275 | 0.725 | 0.010 | 10.792 |

The ablation drop is still 0.000. Even removing all response features from all
history frames does not change aggregate success on this benchmark.

## Interpretation

This is a stronger negative result than the M8 blocker. The current benchmark
does not force the policy to use dynamic response history. The likely remaining
shortcuts are obstacle geometry, path geometry, and label distribution: on this
seed set, M8 succeeds on every sampled `drift_required` case and fails on almost
all `unavoidable` cases, even when response features are masked.

Therefore, the next productive step is not another similar long training run.
The next validation problem must include an online perturbation that cannot be
classified from static obstacle geometry alone.

## Next Gate

Build an online recurrent/closed-loop gate with at least one of:

- delayed friction or actuator changes after the obstacle is already visible;
- hidden-state carry plus hidden-state reset ablation;
- paired scenarios with identical obstacle geometry but different hidden
  vehicle/road response after the first control actions;
- a curriculum that rewards recovery after the perturbation rather than only
  one-shot obstacle pass/fail.

M8 remains the best checkpoint, but it is still not driver v1.
