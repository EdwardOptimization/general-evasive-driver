# M78 Outcome-Weighted Intervention Objective

M77 showed that geometry mining can expose weak history effects, but successful
near-boundary rows still have sub-threshold wrong-history margin loss. M78
starts the training-objective route instead of continuing geometry-only mining.

## Objective

For an outcome-sensitive snippet:

```text
observation o
preferred hidden h+ = normal action-response history
rejected hidden h- = wrong matched history
preferred action a+ = deterministic action under h+
weight w = margin_gap * boundary_weight
```

The auxiliary loss is:

```text
softplus(log pi(a+ | o, h-) - log pi(a+ | o, h+) + margin) * w
```

This is directional:

- it does not force actions to differ everywhere;
- it only emphasizes rows where wrong history reduced clearance margin;
- it keeps actor inputs deployable, using observation, recurrent hidden state,
  and action history only.

## Code Changes

Added training support:

```text
OutcomeInterventionSnippets
load_outcome_intervention_snippets(...)
outcome_weighted_intervention_loss(...)
PPOConfig.outcome_intervention_aux_coef
PPOConfig.outcome_intervention_snapshot_npz
PPOConfig.outcome_intervention_batch_size
PPOConfig.outcome_intervention_logprob_margin
```

Added snapshot-bank export support:

```text
outcome_intervention_snippets.csv
outcome_intervention_snippets.npz
```

The NPZ contains:

```text
observation
preferred_hidden
rejected_hidden
preferred_action
weight
```

Tests added or updated:

```text
tests/test_intervention_objectives.py
tests/test_snapshot_bank_relocation.py
tests/test_checkpoints.py::test_train_logs_outcome_intervention_loss
```

Focused validation:

```text
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  conda run -n autodrift pytest -q \
  tests/test_intervention_objectives.py \
  tests/test_snapshot_bank_relocation.py \
  tests/test_checkpoints.py::test_train_logs_outcome_intervention_loss
```

Result:

```text
15 passed
```

Final validation:

```text
git diff --check
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift pytest -q
```

Result:

```text
215 passed
```

## Snippet Export

Privileged teacher diagnostic export:

```text
runs/m78_outcome_weighted_snippets_seed8601
```

Result:

| Source | Obs Dim | Snippets | Weight Sum | Max Margin Gap |
| --- | ---: | ---: | ---: | ---: |
| M67E privileged teacher | 82 | 523 | 0.247269 | 0.012205 |

Deployable human-view export:

```text
runs/m78_human_view_outcome_weighted_snippets_seed8602
```

Result:

| Source | Obs Dim | Snippets | Weight Sum | Max Margin Gap |
| --- | ---: | ---: | ---: | ---: |
| M62 human-view | 72 | 671 | 0.299190 | 0.010836 |

The M78 training config uses only the human-view 72-dim NPZ:

```text
configs/ppo_m78_outcome_weighted_intervention_driver.json
```

## Smoke Training

Command:

```text
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m78_outcome_weighted_intervention_driver.json \
  --total-steps 4096 \
  --rollout-steps 64 \
  --num-envs 4 \
  --vector-env-mode sync \
  --seed 3368 \
  --device cpu \
  --init-checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --run-dir runs/ppo_m78_outcome_weighted_smoke_seed3368 \
  --eval-episodes 2
```

Result:

```text
run_dir = runs/ppo_m78_outcome_weighted_smoke_seed3368
eval_return_mean = 68.657370
termination_rate = 0.0
final outcome_intervention_loss_mean = 0.038767
```

The train metrics include:

```text
response_prediction_loss_mean
outcome_intervention_loss_mean
baseline_action_anchor_loss_mean
```

## Offline Loss Check

The same human-view snippet NPZ was evaluated against the init checkpoint and
the M78 smoke checkpoint with 20 fixed-seed sampled batches:

| Checkpoint | Mean Loss | Min | Max |
| --- | ---: | ---: | ---: |
| `m62_init` | 0.039923 | 0.031488 | 0.048775 |
| `m78_smoke` | 0.040302 | 0.031875 | 0.049203 |

The smoke checkpoint does not improve the offline objective. This is a negative
training result, not a promotion candidate.

## Interpretation

M78 is an infrastructure pass and a negative smoke result.

What works:

- outcome-weighted snippets can be exported from snapshot-bank relocation;
- the deployable human-view actor can load the snippets;
- PPO logs the new auxiliary loss;
- the actor observation contract stays clean.

What fails:

- a short low-coefficient smoke does not reduce the offline outcome intervention
  loss;
- the snippet weights are very small because current wrong-history effects near
  the boundary are weak;
- the objective may need stronger coefficient, balanced sampling, or direct
  boundary-focused snippets before full continuation is justified.

## Next Step

M79 should tune the objective before long training:

```text
increase or normalize outcome snippet weights
try higher outcome_intervention_aux_coef
sample top-weight snippets more often
compare offline loss before/after over fixed batches
only then run retention and self-ID gates
```

The next pass should treat offline objective reduction as a required smoke gate
before spending GPU time on a full continuation.
