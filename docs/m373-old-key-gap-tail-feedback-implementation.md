# M373 Old-Key Gap-Tail Feedback Implementation

M373 implements the gap-tail feedback path designed in M372. It does not run
PPO, promote a checkpoint, change old-key thresholds, or change actor inputs.

## Implementation

Updated files:

```text
src/autodrift/old_key_preference_corpus.py
src/autodrift/intervention_objectives.py
src/autodrift/exact_post_ppo_repair.py
tests/test_old_key_preference_corpus.py
tests/test_exact_post_ppo_repair.py
```

The old-key overlay loader now accepts a general feedback overlay keyed by
`case_id`. It remains compatible with the M368 hard-row schema and additionally
accepts gap-tail fields:

```text
gap_tail_row
gap_tail_reason
gap_weight_multiplier
normal_branch_weight_multiplier
preferred_branch_weight_multiplier
wrong_branch_weight_multiplier
reference_policy
candidate_policy
reference_margin_gap
candidate_margin_gap
candidate_gap_delta
candidate_normal_delta
candidate_wrong_delta
target_gap_delta_floor
target_gap_delta_buffer
candidate_gap_p10_regression
```

Optional NPZ arrays now include:

```text
hard_row
gap_tail_row
preferred_branch_weight
wrong_branch_weight
```

No-overlay corpora remain in the old compact format. Gap-tail metadata is used
only as training-time repair metadata; deployable actor observations remain the
P0 human-view no-wheel 72-dim frame plus recurrent hidden state.

## Corpus Export

M373 exports a mixed old-key overlay containing:

```text
hard rows: 1
gap-tail rows: 5
```

Overlay:

```text
runs/m373_gap_tail_overlay/old_key_feedback_overlay.csv
```

Weighted corpus:

```text
runs/m373_old_key_preference_corpus_gap_tail/old_key_preference_corpus.npz
runs/m373_old_key_preference_corpus_gap_tail/old_key_preference_corpus.csv
runs/m373_old_key_preference_corpus_gap_tail/summary.json
```

Summary:

| Metric | Value |
| --- | ---: |
| rows | 40 |
| hard rows | 1 |
| gap-tail rows | 5 |
| preferred branch weight sum | 75.628387 |
| wrong branch weight sum | 61.049030 |
| total sample weight sum | 88.349014 |
| actor inputs changed | false |
| PPO or actor update run | false |

The gap-tail rows are the five M371 alpha `0.6` lower-tail rows whose
`candidate_gap_delta` crossed the `-0.0005` design floor.

## No-Update Exact Repair Smoke

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt \
  --raw-checkpoint runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_6.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --old-key-preference-npz runs/m373_old_key_preference_corpus_gap_tail/old_key_preference_corpus.npz \
  --device cpu \
  --start-mode line_search_boundary \
  --line-search-alphas 0,0.4,0.6,1.0 \
  --steps 0 \
  --exact-old-key-tolerance 1e-6 \
  --seed 10109 \
  --run-dir runs/m373_gap_tail_repair_smoke
```

Result:

| Metric | Value |
| --- | ---: |
| selected alpha | 1.0 |
| selected step | 0 |
| exact M297 delta vs base | -0.000068545 |
| exact M270 delta vs base | -0.000033081 |
| old-key surrogate delta vs base | -0.004263401 |
| exact lexicographic pass | true |

This is an integration smoke only. It verifies that the gap-tail weighted
corpus is readable by the exact repair path and that branch weights affect the
old-key surrogate without requiring a training step.

## Validation

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_old_key_preference_corpus.py \
  tests/test_exact_post_ppo_repair.py
```

Result:

```text
16 passed in 0.98s
```

Compile check:

```bash
PYTHONPATH=src python -m compileall -q src tests
```

Result: pass.

## Interpretation

M373 is a positive infrastructure milestone. It makes the M371 gap-tail
failure visible to the differentiable old-key repair surrogate while keeping
closed-loop old-key replay as the authoritative proof gate.

This does not prove that alpha `0.6` is repairable. It only admits a no-PPO
probe that tests whether the new feedback can move beyond the M370 promoted
alpha `0.4` without eroding the old-key compact gap lower tail.

## Decision

Admit:

```text
m374-gap-tail-weighted-repair-probe
```

Decision:

```text
admit_m374_gap_tail_weighted_repair_probe
```
