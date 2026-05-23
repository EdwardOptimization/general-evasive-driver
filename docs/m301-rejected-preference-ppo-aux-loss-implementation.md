# M301 Rejected-Preference PPO Aux-Loss Implementation

M301 implements the M300 training-time PPO guard. No PPO experiment was run, no
actor update was run, and actor inputs are unchanged.

## Implementation

Updated:

```text
src/autodrift/train_ppo.py
tests/test_train_ppo_rejected_preference_aux.py
configs/ppo_m302_rejected_preference_guarded_smoke.json
```

New PPO config fields:

```text
rejected_history_preference_aux_coef
rejected_history_preference_snapshot_npz
rejected_history_preference_batch_size
rejected_history_preference_preferred_logprob_margin
rejected_history_preference_wrong_logprob_margin
rejected_history_preference_wrong_preference_coef
```

Validation requires:

```text
recurrent_sequence_training = true
online recurrent actor encoder
non-empty rejected_history_preference_snapshot_npz
positive batch size
non-negative margins and coefficient
```

The loss uses the M297 helpers:

```text
load_rejected_history_preference_snippets
rejected_history_preference_loss
```

During recurrent PPO sequence updates, `train_ppo` now adds:

```text
loss += rejected_history_preference_aux_coef * rejected_history_preference_loss(...)
```

and records:

```text
rejected_history_preference_loss_mean
rejected_history_preference_aux_coef
```

in `train_metrics.csv`.

## Smoke Config

M301 registers a smoke-scale config for M302:

```text
configs/ppo_m302_rejected_preference_guarded_smoke.json
```

It starts from the M299 public-gate base via CLI:

```text
runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
```

Key PPO settings:

```text
total_steps = 1024
learning_rate = 5e-7
rejected_history_preference_aux_coef = 0.03
outcome_intervention_aux_coef = 0.06
baseline_action_anchor_coef = 100.0
snippet_action_anchor_coef = 100.0
trajectory_action_anchor_coef = 100.0
```

This is intentionally still smoke-scale. The lower learning rate and lower
trajectory anchor coefficient reduce the raw-update pressure that previously
caused M294 to worsen exact M270.

## Validation

Commands:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_train_ppo_rejected_preference_aux.py tests/test_rejected_history_preference_objective.py
python -m compileall -q src tests
make research-validate
PYTHONPATH=src python - <<'PY'
from dataclasses import fields
from autodrift.artifacts import read_json
from autodrift.train_ppo import PPOConfig, is_online_recurrent_encoder, validate_rejected_history_preference_aux_config
raw = read_json('configs/ppo_m302_rejected_preference_guarded_smoke.json')['ppo']
data = {field.name: getattr(PPOConfig(), field.name) for field in fields(PPOConfig)}
for key in data:
    if key in raw:
        data[key] = raw[key]
config = PPOConfig(**data)
validate_rejected_history_preference_aux_config(config, uses_online_recurrent=is_online_recurrent_encoder(config.actor_encoder))
print('m302_config_ok')
PY
```

Results:

```text
5 passed
compileall passed
research validation passed
m302_config_ok
```

## Decision

Admit one smoke-scale guarded PPO run. The next milestone must still reject the
candidate if exact M297, exact M270, M183/M170, M267/M264, protected key, or
behavior retention regresses.

Decision:

```text
admit_m302_rejected_preference_guarded_ppo_smoke
```

Next step:

```text
m302-rejected-preference-guarded-ppo-smoke
```
