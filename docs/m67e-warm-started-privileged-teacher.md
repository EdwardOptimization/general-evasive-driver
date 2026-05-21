# M67-E Warm-Started Privileged Teacher

M67-B showed that a from-scratch privileged `online_gru` teacher is not a
credible upper bound: it never recovered M62's retained emergency-driving
behavior. M67-E tests the narrower question:

```text
Can a teacher preserve M62's 72-value human-view behavior first,
then use hidden dynamics as an extra teacher-only context branch
to improve M65 response-critical clearance margin?
```

## Implementation

New actor encoder:

```text
privileged_human_view_online_gru
```

Observation contract:

```text
0-71   unchanged human-view frame
72-81  full hidden dynamics packet, teacher-only
```

The response/context path is intentionally M62-compatible:

```text
response/action stream 0-11 -> response_encoder -> GRUCell -> hidden
scene/context stream 12-71 -> context_encoder
policy feature = fusion(hidden, context, hidden * context)
```

The privileged packet enters through a separate branch:

```text
privileged 72-81 -> privileged_encoder
feature = base_feature + zero_init_residual(base_feature, privileged, product)
```

The residual is zero-initialized. Loading `m62_a250` into the teacher returns:

```text
partial_privileged_human_view_branch
```

This means all compatible M62 tensors load normally, while only the new
privileged branch starts from target initialization. Because the residual starts
at zero, initial deterministic actions, values, and recurrent hidden updates are
identical to the human-view path for the same first 72 values.

Artifacts:

- `src/autodrift/train_ppo.py`
- `src/autodrift/checkpoints.py`
- `configs/ppo_m67e_warm_started_privileged_teacher.json`
- `tests/test_checkpoints.py`
- `tests/test_privileged_upper_bound.py`

## Validation

Focused tests:

```text
conda run -n autodrift pytest -q \
  tests/test_checkpoints.py::test_privileged_human_view_init_preserves_human_view_behavior \
  tests/test_checkpoints.py::test_privileged_human_view_online_actor_checkpoint_loads \
  tests/test_privileged_upper_bound.py::test_m67e_warm_started_privileged_teacher_config_uses_strict_teacher_frame
```

Result:

```text
3 passed
```

Broader targeted suite:

```text
conda run -n autodrift pytest -q tests/test_checkpoints.py tests/test_privileged_upper_bound.py tests/test_env.py -q
```

Result:

```text
60 passed
```

Compile and whitespace checks:

```text
python -m compileall -q src tests
git diff --check
```

Both passed before the experiment runs.

## Smoke Run

Command:

```text
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --total-steps 4096 \
  --rollout-steps 64 \
  --num-envs 4 \
  --vector-env-mode sync \
  --seed 3267 \
  --device cuda \
  --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --run-dir runs/ppo_m67e_warm_privileged_teacher_smoke_seed3267 \
  --eval-episodes 2
```

Key output:

```text
loaded_init_checkpoint=... load_mode=partial_privileged_human_view_branch
loaded_baseline_action_anchor=... load_mode=partial_privileged_human_view_branch
eval return mean: 70.071778
eval termination rate: 0.000000
```

Smoke upper-bound command:

```text
conda run -n autodrift python -m autodrift.privileged_upper_bound \
  --baseline-env-config configs/ppo_m67d_strict_self_id_context_driver.json \
  --candidate-env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --baseline-checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --candidate-checkpoint-policy m67e_smoke=runs/ppo_m67e_warm_privileged_teacher_smoke_seed3267/checkpoint.pt \
  --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv \
  --seed 3600 \
  --device cpu \
  --run-dir runs/m67e_warm_privileged_teacher_smoke_upper_bound_m65_seed3600
```

Smoke result on M65:

| Policy | Success | Mean Margin |
| --- | ---: | ---: |
| `m62_a250` | 0.615385 | 0.259881 |
| `m67e_smoke` | 0.615385 | 0.259679 |

Interpretation: the architecture preserves M62-class behavior after a small
update, but the smoke checkpoint is not an upper-bound result.

## 32768-Step Run

Command:

```text
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --seed 3267 \
  --device cuda \
  --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --run-dir runs/ppo_m67e_warm_privileged_teacher_seed3267
```

Key output:

```text
loaded_init_checkpoint=... load_mode=partial_privileged_human_view_branch
loaded_baseline_action_anchor=... load_mode=partial_privileged_human_view_branch
step=20480 update=5 rollout_return_mean=60.61
step=32768 update=8 rollout_return_mean=56.92
eval return mean: 63.859678
eval termination rate: 0.100000
```

Final upper-bound command:

```text
conda run -n autodrift python -m autodrift.privileged_upper_bound \
  --baseline-env-config configs/ppo_m67d_strict_self_id_context_driver.json \
  --candidate-env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --baseline-checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --candidate-checkpoint-policy m67e_final=runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoint.pt \
  --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv \
  --seed 3600 \
  --device cpu \
  --run-dir runs/m67e_warm_privileged_teacher_upper_bound_m65_seed3600
```

Final result on M65:

| Policy | Success | Mean Margin | Mean Margin Delta |
| --- | ---: | ---: | ---: |
| `m62_a250` | 0.615385 | 0.259881 | 0.000000 |
| `m67e_final` | 0.615385 | 0.258980 | -0.000901 |

The final checkpoint is not better than M62.

## Checkpoint Sweep

Command:

```text
conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv \
  --checkpoint-policy m67e_004=runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --checkpoint-policy m67e_008=runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_8192.pt \
  --checkpoint-policy m67e_012=runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_12288.pt \
  --checkpoint-policy m67e_016=runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_16384.pt \
  --checkpoint-policy m67e_020=runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_20480.pt \
  --checkpoint-policy m67e_024=runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_24576.pt \
  --checkpoint-policy m67e_028=runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_28672.pt \
  --checkpoint-policy m67e_032=runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_32768.pt \
  --policies heuristic \
  --device cpu \
  --run-dir runs/m67e_warm_privileged_teacher_checkpoint_sweep_m65_seed3600
```

Sweep result:

| Policy | Success | Mean Margin | Min Margin |
| --- | ---: | ---: | ---: |
| `m67e_004` | 0.615385 | 0.260685 | -0.181427 |
| `m67e_008` | 0.615385 | 0.256264 | -0.173237 |
| `m67e_012` | 0.615385 | 0.257312 | -0.163007 |
| `m67e_016` | 0.615385 | 0.258782 | -0.153376 |
| `m67e_020` | 0.615385 | 0.259282 | -0.146352 |
| `m67e_024` | 0.615385 | 0.256277 | -0.138726 |
| `m67e_028` | 0.615385 | 0.257648 | -0.131055 |
| `m67e_032` | 0.615385 | 0.258980 | -0.122912 |

The best mean-margin checkpoint is `m67e_004`.

Best upper-bound command:

```text
conda run -n autodrift python -m autodrift.privileged_upper_bound \
  --baseline-env-config configs/ppo_m67d_strict_self_id_context_driver.json \
  --candidate-env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --baseline-checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --candidate-checkpoint-policy m67e_004=runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv \
  --seed 3600 \
  --device cpu \
  --run-dir runs/m67e_warm_privileged_teacher_best_upper_bound_m65_seed3600
```

Best result summary:

| Metric | `m62_a250` | `m67e_004` | Delta |
| --- | ---: | ---: | ---: |
| Success | 0.615385 | 0.615385 | 0.000000 |
| Collision rate | 0.384615 | 0.384615 | 0.000000 |
| Mean clearance margin | 0.259881 | 0.260685 | 0.000804 |
| Margin-improved seeds | - | 13 / 26 | - |
| Margin-regressed seeds | - | 13 / 26 | - |

## Conclusion

M67-E is a successful infrastructure step and a weak/negative upper-bound
result.

What it proves:

- the M62-compatible privileged human-view teacher architecture works;
- `m62_a250` can initialize and anchor the 82-value teacher without changing the
  first-step behavior;
- training does not immediately wash out M62 success on the M65 response-critical
  corpus.

What it does not prove:

- hidden dynamics creates a meaningful oracle upper-bound gap on the current M65
  corpus;
- the current corpus contains enough matched states where hidden dynamics should
  change the correct action;
- a deployable student should be trained from this teacher yet.

The best M67-E checkpoint improves mean margin by only `0.000804` with an even
13/13 improved/regressed seed split. Treat this as retention noise, not as a
teacher breakthrough.

## Next Step

Do not proceed directly to teacher-student OSI training.

The next milestone should mine a matched action-divergent corpus:

```text
same or near-same current visible state
same or near-same road / obstacle geometry
different hidden dynamics
teacher / oracle / rollout outcome requires different action
wrong hidden or wrong history reduces clearance margin
```

If such pairs cannot be found, the current M65 response-necessity corpus is not
the right proof surface for self-identification. If they can be found, the
project can build wrong-history interventions and teacher-student distillation
around those cases.
