# M80 Outcome Objective-Only Sanity Check

M78 and M79 showed that PPO-integrated outcome intervention training can move
the fixed-batch objective in the wrong direction. M80 isolates the objective
from PPO rollouts, advantages, and baseline anchors.

## Hypothesis

If `outcome_weighted_intervention_loss` is correctly signed and the M78
human-view snippets contain usable signal, then direct optimization of only this
loss from `m62_a250` should reduce the same fixed-batch loss used by the M79
evaluator.

If it cannot decrease in isolation, the objective, data, or sign must be fixed
before any more PPO continuation.

## Harness

Added:

```text
src/autodrift/outcome_intervention_optimize.py
tests/test_outcome_intervention_optimize.py
```

The harness:

- loads a checkpoint and one outcome intervention snippet NPZ;
- freezes `log_std` by default to avoid a variance-only false positive;
- optimizes only `outcome_weighted_intervention_loss`;
- saves `optimized_checkpoint.pt`;
- evaluates before/after with the M79 fixed-batch evaluator seed;
- writes `train_metrics.csv`, `policy_summary.csv`, `batch_losses.csv`, and
  `summary.json`.

Focused validation:

```text
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  conda run -n autodrift pytest -q \
  tests/test_outcome_intervention_optimize.py \
  tests/test_outcome_intervention_eval.py \
  tests/test_intervention_objectives.py
git diff --check
```

Result:

```text
13 passed
```

## Objective-Only Run

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.outcome_intervention_optimize \
  --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --snippet-npz runs/m78_human_view_outcome_weighted_snippets_seed8602/outcome_intervention_snippets.npz \
  --device cpu \
  --steps 200 \
  --batch-size 256 \
  --learning-rate 0.0001 \
  --logprob-margin 0.05 \
  --seed 8800 \
  --grad-clip-norm 1.0 \
  --log-interval 20 \
  --eval-batch-size 128 \
  --eval-batches 20 \
  --eval-seed 0 \
  --run-dir runs/m80_outcome_objective_only_seed8800
```

Result:

| Policy | Mean Loss | Std | Min | Max |
| --- | ---: | ---: | ---: | ---: |
| `before` | 0.039923 | 0.003851 | 0.031488 | 0.048775 |
| `after` | 0.008483 | 0.001211 | 0.005603 | 0.011761 |

Training loss also moved down during the 200 objective-only steps:

| Step | Training Loss |
| ---: | ---: |
| 120 | 0.031020 |
| 140 | 0.026315 |
| 160 | 0.023347 |
| 180 | 0.021830 |
| 200 | 0.017400 |

Artifact:

```text
runs/m80_outcome_objective_only_seed8800/summary.json
```

Conclusion: the isolated objective passes the sanity check. The M78/M79 failure
is not explained by a reversed loss sign or completely unusable snippets.

## Short Driving Smoke

The optimized checkpoint is not promoted by this result, but it should not be
treated as unusable solely because it was trained offline. A 5-episode
same-seed smoke compared M62 and the objective-only checkpoint:

```text
M62 run: runs/m80_m62_eval_seed8800
M80 run: runs/m80_outcome_objective_only_eval_seed8800
```

| Policy | Return Mean | Termination | Min Clearance Mean | Min Clearance Min |
| --- | ---: | ---: | ---: | ---: |
| `m62_a250` | 79.328658 | 0.0 | 3.696820 | 2.329961 |
| `m80_objective_only` | 85.073736 | 0.0 | 3.715574 | 2.488389 |

This is only a smoke check, not a promotion gate. It says the objective-only
update did not immediately destroy basic 5-seed driving behavior.

## Interpretation

M80 is a positive objective sanity result:

- the outcome intervention objective can decrease from `m62_a250`;
- fixed-batch loss improves by `0.031440`;
- freezing `log_std` did not block optimization;
- the short driving smoke does not reveal an immediate collapse.

What M80 does not prove:

- no strict margin-retention gate was run;
- no paired self-identification gate was run;
- no PPO-integrated continuation was fixed;
- no wheel/tire input gap was addressed.

## Final Validation

```text
git diff --check
python -m compileall -q src tests
python -m json.tool experiments/research_status.json
python csv validation for experiments/research_queue.csv
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift pytest -q
```

Result:

```text
218 passed in 2.59s
```

## Next Step

The next queued task remains M81: add deployable wheel/tire response signals and
wheel-specific self-identification gates. The M80 result should also be used
later for a smaller PPO reintroduction:

```text
low learning rate
freeze log_std or monitor log_std drift
fixed-batch objective guard
strict margin-retention guard
short same-seed eval guard
```

For now, the larger bottleneck identified by the MHTML review is that the
current 72-value input lacks wheel/tire feedback for a professional-driver-like
self-identification claim.
