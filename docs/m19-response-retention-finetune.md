# M19 Response-Retention Fine-Tune

Last updated: 2026-05-21

## Motivation

M18 is a meaningful step toward closed-loop self-identification: response
masking and hidden-state reset both hurt paired-gate performance. The cost is
aggregate success. M18's actuator-response gate remains low-success, and M13
friction perturbed success is `0.375`, below M17's `0.400`.

M19 is a same-contract fine-tune from the M18 checkpoint. The goal is to recover
success while preserving the response-dependence signal that M18 created.

## Training Config

Config:

```text
configs/ppo_m19_response_retention_finetune_driver.json
```

Queued command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m19_response_retention_finetune_driver.json \
  --seed 919 \
  --device cuda \
  --init-checkpoint runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt \
  --run-dir runs/ppo_m19_response_retention_finetune_seed919
```

The M19 distribution softens the hardest actuator ranges from M18:

- `actuator_tau_scale_range`: `[0.55, 2.85]` in base, with a response-retention
  curriculum stage up to `[0.55, 3.05]`;
- `brake_scale_range`: `[0.55, 1.35]`;
- `drive_scale_range`: `[0.60, 1.30]`;
- `tire_stiffness_scale_range`: `[0.58, 1.42]`.

It keeps the online-GRU deployable actor contract and does not use privileged
parameters, labels, controller modes, explicit sideslip, speed references, or
response-prediction auxiliary loss.

Smoke result:

- command: `conda run -n autodrift python -m autodrift.train_ppo --config configs/ppo_m19_response_retention_finetune_driver.json --total-steps 20480 --seed 919 --device cuda --init-checkpoint runs/ppo_m18_actuator_response_recurrent_seed911/checkpoint.pt --run-dir runs/ppo_m19_response_retention_smoke_seed919`;
- init checkpoint load mode: `strict`;
- run dir: `runs/ppo_m19_response_retention_smoke_seed919`;
- eval return mean: 72.061;
- eval steps mean: 63.300;
- eval termination rate: 0.100;
- eval lateral RMSE mean: 0.950;
- eval beta absolute error mean: 0.173.

## Pass Direction

M19 should be considered useful only if it improves success without erasing the
M18 response-dependence signal:

- M13 friction perturbed success should recover to at least M17's `0.400`;
- actuator-response gate perturbed success should beat M18's `0.375`;
- normal recurrent inference should beat `reset_recurrent_state`;
- `zero_current_response` and `zero_all_response` should remain worse than
  normal recurrent inference;
- same-corpus obstacle benchmark should stay above envelope AES and avoid
  drift-seeking stable-AES behavior.
