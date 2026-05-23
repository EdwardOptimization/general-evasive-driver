# M363 Old-Key-Aware Repair Implementation

M363 implements the old-key-aware exact repair infrastructure designed in M362.
It does not run PPO, promote a checkpoint, or change actor inputs.

## Code Changes

New module:

```text
src/autodrift/old_key_preference_corpus.py
```

Responsibilities:

- convert M341 compact old-key neighborhood rows into an NPZ compatible with
  rejected-history preference snippets;
- store only deployable observation plus recurrent hidden/action-response state
  tensors needed for training-time repair;
- write metadata CSV and summary JSON;
- validate shapes, finite values, positive weights, group count, target count,
  and actor-input contract.

Extended module:

```text
src/autodrift/exact_post_ppo_repair.py
```

New optional arguments:

```text
--old-key-preference-npz
--old-key-preferred-logprob-margin
--old-key-wrong-logprob-margin
--old-key-wrong-preference-coef
--exact-old-key-tolerance
--lambda-old-key
--lambda-old-key-anchor
```

When `--old-key-preference-npz` is omitted, existing exact repair behavior is
unchanged.

## Old-Key Surrogate

The repair tool now records optional metrics:

```text
old_key_surrogate_loss
old_key_preference_loss
old_key_action_anchor_loss
old_key_surrogate_delta_vs_base
old_key_surrogate_no_regression
hinge_old_key
```

The lexicographic pass now includes old-key surrogate no-regression only when an
old-key corpus is provided.

## Real Corpus Export

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.old_key_preference_corpus \
  --reference-manifest runs/m341_old_key_neighborhood_block_a_seed9860/manifest.json \
  --compact-corpus-csv runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv \
  --base-checkpoint runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt \
  --device cpu \
  --run-dir runs/m363_old_key_preference_corpus
```

Result:

```text
rows = 40
```

Artifacts:

```text
runs/m363_old_key_preference_corpus/old_key_preference_corpus.npz
runs/m363_old_key_preference_corpus/old_key_preference_corpus.csv
runs/m363_old_key_preference_corpus/summary.json
```

## Repair Integration Smoke

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt \
  --raw-checkpoint runs/m356_m354_repair_best_step_probe/candidate_checkpoint.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --old-key-preference-npz runs/m363_old_key_preference_corpus/old_key_preference_corpus.npz \
  --device cpu \
  --start-mode line_search_boundary \
  --line-search-alphas 0,0.00025,0.0005 \
  --steps 0 \
  --seed 10104 \
  --run-dir runs/m363_old_key_repair_smoke
```

Result:

```text
old_key_rows: 40
selected_alpha: 0.0
candidate old_key_surrogate_delta_vs_base: 0.0
candidate exact_lexicographic_pass: true
selection_trace_csv: runs/m363_old_key_repair_smoke/selection_trace.csv
```

This is an integration smoke only. `steps=0` intentionally performs no repair
update and should not be interpreted as driver progress.

## Tests

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_old_key_preference_corpus.py \
  tests/test_exact_post_ppo_repair.py
```

Result:

```text
11 passed
```

Compile check:

```bash
PYTHONPATH=src python -m compileall -q src tests
```

Result: pass.

## Decision

M363 completes the infrastructure implementation. The next step is a no-PPO
probe that actually runs old-key-aware repair steps against the M356 best-step
direction and then checks exact, old-key targeted replay, source-diverse, and
first replay gates.

Admit:

```text
m364-old-key-aware-repair-probe
```

Decision:

```text
admit_m364_old_key_aware_repair_probe
```
