# M368 Old-Key Hard-Row Feedback Implementation

M368 implements the hard-row feedback path designed in M367. It does not run
PPO, promote a checkpoint, lower old-key thresholds, or change actor inputs.

## Code Changes

Extended module:

```text
src/autodrift/old_key_preference_corpus.py
```

New behavior:

- computes stable old-key `case_id` values;
- optionally loads a hard-row overlay CSV;
- merges hard-row metadata by `case_id`;
- multiplies row weights with `hard_weight_multiplier`;
- writes optional NPZ arrays:
  `hard_row`, `preferred_branch_weight`, `wrong_branch_weight`;
- preserves the old NPZ contract when no overlay is provided.

Extended module:

```text
src/autodrift/intervention_objectives.py
```

The rejected-history preference loader now accepts the optional hard-row and
branch-weight arrays. Existing corpora without these arrays still load
unchanged.

Extended module:

```text
src/autodrift/exact_post_ppo_repair.py
```

The old-key surrogate uses branch weights only when the optional arrays are
present. If absent, the previous old-key surrogate path is preserved exactly.

## Hard-Row Overlay

Overlay artifact:

```text
runs/m368_hard_row_overlay/hard_row_overlay.csv
```

It marks the M366 sign-crossing row:

```text
9951|perturbed|35|32|10.000000|-1.200000|1.400000
```

with:

```text
hard_weight_multiplier = 8.0
preferred_branch_weight_multiplier = 1.0
wrong_branch_weight_multiplier = 16.0
```

The overlay is training-time metadata only. It is not actor observation.

## Weighted Corpus Export

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.old_key_preference_corpus \
  --reference-manifest runs/m341_old_key_neighborhood_block_a_seed9860/manifest.json \
  --compact-corpus-csv runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv \
  --base-checkpoint runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt \
  --hard-row-overlay-csv runs/m368_hard_row_overlay/hard_row_overlay.csv \
  --device cpu \
  --run-dir runs/m368_old_key_preference_corpus_hard_row
```

Result:

```text
rows = 40
hard_rows = 1
preferred_branch_weight sum = 40.0
wrong_branch_weight sum = 55.0
```

Artifacts:

```text
runs/m368_old_key_preference_corpus_hard_row/old_key_preference_corpus.npz
runs/m368_old_key_preference_corpus_hard_row/old_key_preference_corpus.csv
runs/m368_old_key_preference_corpus_hard_row/summary.json
```

## Repair Integration Smoke

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt \
  --raw-checkpoint runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_2.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --old-key-preference-npz runs/m368_old_key_preference_corpus_hard_row/old_key_preference_corpus.npz \
  --device cpu \
  --start-mode line_search_boundary \
  --line-search-alphas 0,0.25,0.5,1.0 \
  --steps 0 \
  --exact-old-key-tolerance 1e-6 \
  --seed 10107 \
  --run-dir runs/m368_hard_row_repair_smoke
```

Result:

```text
old_key_rows = 40
old_key_surrogate_no_regression = true
exact_m297_no_regression = true
exact_m270_no_regression = true
exact_lexicographic_pass = true
steps = 0
```

This is an integration smoke only. It verifies the weighted corpus can be read
by exact repair; it does not claim a repaired driver improvement.

## Tests

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_old_key_preference_corpus.py \
  tests/test_exact_post_ppo_repair.py
```

Result:

```text
14 passed
```

Compile check:

```bash
PYTHONPATH=src python -m compileall -q src tests
```

Result: pass.

## Interpretation

M368 makes replay-discovered hard rows visible to the differentiable old-key
repair path. It preserves backward compatibility and the actor-input contract.

The next step must be a no-PPO probe that actually attempts a hard-row weighted
repair and then checks closed-loop old-key replay. The surrogate remains a
guide; old-key replay remains the proof gate.

## Decision

Admit:

```text
m369-hard-row-weighted-repair-probe
```

Decision:

```text
admit_m369_hard_row_weighted_repair_probe
```
