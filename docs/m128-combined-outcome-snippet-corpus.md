# M128 Combined Outcome Snippet Corpus

M127 admits the strict zero-relvel wrong-history outcome surface, but the
accepted snippets were spread across three miner runs. M128 builds one
accepted-only corpus before any new objective or PPO run.

## Tooling

M128 adds:

```text
src/autodrift/outcome_snippet_corpus.py
tests/test_outcome_snippet_corpus.py
```

The combiner validates:

- every input run has `manifest.json` with
  `outcome_export.only_accepted_outcomes=true`;
- every input NPZ has `observation`, `preferred_hidden`, `rejected_hidden`,
  `preferred_action`, and `weight`;
- NPZ row counts match CSV metadata row counts;
- metadata weights match NPZ weights;
- all weights are positive and finite;
- deduplicated rows preserve `source_runs`, `source_row_indices`, and
  `source_run_count`.

## Command

```text
PYTHONPATH=src python -m autodrift.outcome_snippet_corpus \
  --input-run runs/m126_zero_relvel_m124_strict_60ep_seed9720 \
  --input-run runs/m127_zero_relvel_m124_strict_60ep_seed9820 \
  --input-run runs/m127_zero_relvel_m124_strict_60ep_seed9840 \
  --deduplicate \
  --run-dir runs/m128_combined_outcome_snippet_corpus
```

## Artifacts

```text
runs/m128_combined_outcome_snippet_corpus/outcome_intervention_snippets.npz
runs/m128_combined_outcome_snippet_corpus/outcome_intervention_snippets.csv
runs/m128_combined_outcome_snippet_corpus/summary.json
runs/m128_combined_outcome_snippet_corpus/manifest.json
```

The combined NPZ loads through the existing training-time loader:

```text
size=44
observation=(44, 72)
preferred_hidden=(44, 128)
rejected_hidden=(44, 128)
preferred_action=(44, 3)
weight=(44,)
weight_sum=0.419241
```

## Result

| Metric | Value |
| --- | ---: |
| Input runs | 3 |
| Input rows | 62 |
| Output rows | 44 |
| Duplicate rows removed | 18 |
| Unique seeds | 13 |
| Weight sum | 0.419241 |
| Weight min | 0.002719 |
| Weight max | 0.034211 |

Contributing source-run counts before deduplication:

| Source run | Rows |
| --- | ---: |
| `runs/m126_zero_relvel_m124_strict_60ep_seed9720` | 14 |
| `runs/m127_zero_relvel_m124_strict_60ep_seed9820` | 24 |
| `runs/m127_zero_relvel_m124_strict_60ep_seed9840` | 24 |

Primary source-run counts after deduplication:

| Source run | Rows |
| --- | ---: |
| `runs/m126_zero_relvel_m124_strict_60ep_seed9720` | 14 |
| `runs/m127_zero_relvel_m124_strict_60ep_seed9820` | 24 |
| `runs/m127_zero_relvel_m124_strict_60ep_seed9840` | 6 |

Source-side coverage remains:

```text
{'perturbed': 44}
```

This is still a perturbed-side low-friction proof surface, not a symmetric
nominal/perturbed corpus.

## Decision

M128 passes as infrastructure. The combined corpus is ready for objective
sanity testing, but it is not itself a driver result.

What improved:

- M127 accepted snippets are now one reproducible NPZ/CSV pair;
- duplicate snippets from overlapping miner seeds are removed;
- each retained row keeps source-run provenance;
- the existing `load_outcome_intervention_snippets` loader accepts the corpus.

Remaining limits:

- all rows are perturbed-source;
- the corpus encodes wrong-history outcome degradation, not no-action history;
- PPO remains blocked until an objective-sanity run and behavior gates pass.

Next step: M129 should test a retention-anchored objective on the deduplicated
M128 corpus before any PPO continuation.
