# M82 Outcome Objective PPO Reintroduction

M80 proved that `outcome_weighted_intervention_loss` can decrease outside PPO.
M82 tests a guarded PPO reintroduction before spending on a full continuation.

## Hypothesis

If M78/M79 failed partly because PPO moved too aggressively or exploited policy
variance, then a lower learning rate plus frozen `log_std` should move the
fixed-batch outcome objective closer to M80's direction while preserving basic
driving behavior.

## Code And Config

Added:

```text
PPOConfig.freeze_log_std
configs/ppo_m82_outcome_guarded_reintro_driver.json
```

The trainer now supports freezing the actor `log_std` parameter before optimizer
construction. This is a guard against objective improvement that comes only from
changing policy variance.

Focused validation:

```text
python -m json.tool configs/ppo_m82_outcome_guarded_reintro_driver.json
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  conda run -n autodrift pytest -q \
  tests/test_checkpoints.py::test_train_can_freeze_log_std \
  tests/test_checkpoints.py::test_train_logs_outcome_intervention_loss \
  tests/test_outcome_intervention_eval.py
git diff --check
```

Result:

```text
4 passed
```

## Guarded PPO Smoke

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m82_outcome_guarded_reintro_driver.json \
  --total-steps 4096 \
  --rollout-steps 64 \
  --num-envs 4 \
  --vector-env-mode sync \
  --seed 3682 \
  --device cpu \
  --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --run-dir runs/ppo_m82_outcome_guarded_smoke_seed3682 \
  --eval-episodes 2
```

Result:

```text
run_dir = runs/ppo_m82_outcome_guarded_smoke_seed3682
eval_return_mean = 30.307775
termination_rate = 0.5
final train outcome_intervention_loss_mean = 0.077532
```

The short eval is not acceptable for promotion.

## Fixed-Batch Objective Guard

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.outcome_intervention_eval \
  --snippet-npz runs/m78_human_view_outcome_weighted_snippets_seed8602/outcome_intervention_snippets.npz \
  --checkpoint-policy m62_init=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m78_smoke=runs/ppo_m78_outcome_weighted_smoke_seed3368/checkpoint.pt \
  --checkpoint-policy m79_highcoef=runs/ppo_m79_outcome_weighted_highcoef_smoke_seed3469/checkpoint.pt \
  --checkpoint-policy m82_guarded=runs/ppo_m82_outcome_guarded_smoke_seed3682/checkpoint.pt \
  --device cpu \
  --batch-size 128 \
  --batches 20 \
  --seed 0 \
  --logprob-margin 0.05 \
  --run-dir runs/m82_outcome_intervention_eval_seed0
```

Result:

| Policy | Mean Loss | Std | Min | Max |
| --- | ---: | ---: | ---: | ---: |
| `m62_init` | 0.039923 | 0.003851 | 0.031488 | 0.048775 |
| `m78_smoke` | 0.040302 | 0.003866 | 0.031875 | 0.049203 |
| `m79_highcoef` | 0.041033 | 0.003904 | 0.032635 | 0.050051 |
| `m82_guarded` | 0.040120 | 0.003857 | 0.031694 | 0.048996 |

M82 improves over M78/M79 but still does not beat the M62 fixed-batch baseline.

## Interpretation

M82 is a guarded-integration improvement, but still a negative gate result:

- freezing `log_std` works mechanically;
- lower learning rate and frozen variance reduce the PPO objective regression
  relative to M78/M79;
- fixed-batch loss is still worse than `m62_init`;
- the 2-episode driving smoke terminates in one episode.

Do not run a long outcome-objective continuation yet. The likely next
integration needs one or more of:

- pretrain objective-only for a small number of steps, then PPO with stronger
  retention;
- reduce outcome objective weight further and add a hard fixed-batch guard
  between checkpoint intervals;
- apply the objective only on batches with better margin/weight quality;
- revisit snippet quality after wheel-response input is trained.

## Final Validation

```text
git diff --check
python -m compileall -q src tests
python -m json.tool experiments/research_status.json
python -m json.tool configs/ppo_m82_outcome_guarded_reintro_driver.json
python csv validation for experiments/research_queue.csv
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift pytest -q
```

Result:

```text
226 passed in 2.26s
```

## Next Step

Move to M83: train and gate the new 85-value wheel-response driver. M81 created
the sensory channel; M82 shows the old 72-value PPO objective branch is still
not enough to promote a better driver.
