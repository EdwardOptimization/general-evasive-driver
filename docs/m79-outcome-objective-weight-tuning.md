# M79 Outcome Objective Weight Tuning

M78 wired the outcome-weighted intervention loss into PPO, but the first short
smoke did not reduce fixed-batch offline loss. M79 makes that offline check a
reusable harness and tests a stronger coefficient before any full continuation.

## Fixed-Batch Evaluator

Added:

```text
src/autodrift/outcome_intervention_eval.py
tests/test_outcome_intervention_eval.py
```

The evaluator loads one snippet NPZ and one or more checkpoints, resets the Torch
RNG to the same seed for every checkpoint, and reports the same sampled-batch
loss distribution:

```text
policy_summary.csv
batch_losses.csv
summary.json
```

Focused validation:

```text
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  conda run -n autodrift pytest -q \
  tests/test_outcome_intervention_eval.py tests/test_intervention_objectives.py
```

Result:

```text
12 passed
```

## Baseline Reproduction

Command:

```text
conda run -n autodrift python -m autodrift.outcome_intervention_eval \
  --snippet-npz runs/m78_human_view_outcome_weighted_snippets_seed8602/outcome_intervention_snippets.npz \
  --checkpoint-policy m62_init=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m78_smoke=runs/ppo_m78_outcome_weighted_smoke_seed3368/checkpoint.pt \
  --device cpu \
  --batch-size 128 \
  --batches 20 \
  --seed 0 \
  --logprob-margin 0.05 \
  --run-dir runs/m79_outcome_intervention_eval_m78_seed0
```

Result:

| Policy | Mean Loss | Std | Min | Max |
| --- | ---: | ---: | ---: | ---: |
| `m62_init` | 0.039923 | 0.003851 | 0.031488 | 0.048775 |
| `m78_smoke` | 0.040302 | 0.003866 | 0.031875 | 0.049203 |

This reproduces the M78 conclusion with a committed harness.

## High-Coefficient Smoke

Added:

```text
configs/ppo_m79_outcome_weighted_highcoef_driver.json
```

Changes versus M78:

```text
learning_rate = 5e-6
outcome_intervention_aux_coef = 0.3
outcome_intervention_batch_size = 256
```

Smoke command:

```text
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m79_outcome_weighted_highcoef_driver.json \
  --total-steps 4096 \
  --rollout-steps 64 \
  --num-envs 4 \
  --vector-env-mode sync \
  --seed 3469 \
  --device cpu \
  --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --run-dir runs/ppo_m79_outcome_weighted_highcoef_smoke_seed3469 \
  --eval-episodes 2
```

Result:

```text
run_dir = runs/ppo_m79_outcome_weighted_highcoef_smoke_seed3469
eval_return_mean = 49.376177
termination_rate = 0.5
final train outcome_intervention_loss_mean = 0.078022
```

The higher coefficient worsens the short eval relative to M78.

## Offline Check

Command:

```text
conda run -n autodrift python -m autodrift.outcome_intervention_eval \
  --snippet-npz runs/m78_human_view_outcome_weighted_snippets_seed8602/outcome_intervention_snippets.npz \
  --checkpoint-policy m62_init=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m78_smoke=runs/ppo_m78_outcome_weighted_smoke_seed3368/checkpoint.pt \
  --checkpoint-policy m79_highcoef=runs/ppo_m79_outcome_weighted_highcoef_smoke_seed3469/checkpoint.pt \
  --device cpu \
  --batch-size 128 \
  --batches 20 \
  --seed 0 \
  --logprob-margin 0.05 \
  --run-dir runs/m79_outcome_intervention_eval_highcoef_seed0
```

Result:

| Policy | Mean Loss | Std | Min | Max |
| --- | ---: | ---: | ---: | ---: |
| `m62_init` | 0.039923 | 0.003851 | 0.031488 | 0.048775 |
| `m78_smoke` | 0.040302 | 0.003866 | 0.031875 | 0.049203 |
| `m79_highcoef` | 0.041033 | 0.003904 | 0.032635 | 0.050051 |

M79 does not pass the offline objective gate.

## Interpretation

M79 is an infrastructure pass and a negative coefficient-tuning result.

What works:

- fixed-batch offline evaluation is now a committed reproducible harness;
- the M78 negative result is reproducible;
- a high-coefficient smoke runs and can be compared automatically.

What fails:

- increasing coefficient and learning rate makes the offline objective worse;
- the high-coefficient smoke also hurts short evaluation termination rate;
- the problem is likely not just coefficient scale.

## Final Validation

```text
git diff --check
python -m compileall -q src tests
python -m json.tool experiments/research_status.json
python -m json.tool configs/ppo_m79_outcome_weighted_highcoef_driver.json
python csv validation for experiments/research_queue.csv
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift pytest -q
```

Result:

```text
217 passed in 3.74s
```

## Next Step

M80 should isolate the loss outside PPO:

```text
optimize only outcome_intervention_loss on the NPZ from m62_init
measure fixed-batch loss before/after
if loss cannot decrease, fix the objective/sign/data
if loss can decrease, reintroduce PPO/anchor gradually
```

This is the cleanest next blocker because M79 shows PPO updates can move the
objective in the wrong direction even when the coefficient is stronger.
