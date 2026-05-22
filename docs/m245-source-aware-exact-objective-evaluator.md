# M245 Source-Aware Exact Objective Evaluator

M245 turns the M244 ad hoc per-source audit into a durable evaluator feature.
No PPO was run and actor inputs are unchanged.

## Change

`autodrift.outcome_intervention_eval` now supports named source corpora in exact
mode:

```text
--exact
--source-npz NAME=PATH
--baseline-policy POLICY_NAME
```

When source corpora are provided, the evaluator strictly matches every combined
corpus row to exactly one named source by:

```text
observation
preferred_hidden
rejected_hidden
preferred_action
```

It emits:

```text
policy_summary.csv
batch_losses.csv
source_summary.csv
per_row_losses.csv
summary.json
```

The source reports use the same denominator rule as `weighted_mean`: source and
combined denominators are clamped to at least `1.0`.

## Reproduction

Run directory:

```text
runs/m245_source_aware_exact_m232_eval
```

Command shape:

```text
python -m autodrift.outcome_intervention_eval --exact \
  --snippet-npz runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz \
  --source-npz m223=runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz \
  --source-npz protected_key=runs/m231_protected_key_snippet_surface/protected_key_snippets.npz \
  --baseline-policy m239_a500 \
  --checkpoint-policy ...
```

M245 exactly reproduces the M244 source deltas:

```text
max_abs_diff_vs_m244_source_deltas = 0.0
```

| Policy | M223 delta | Protected-key delta |
| --- | ---: | ---: |
| m243_a100 | -0.000000821309 | 0.000001015703 |
| m243_a250 | -0.000001983192 | 0.000002556134 |
| m243_a500 | -0.000003888495 | 0.000005152159 |
| m243_a750 | -0.000005702850 | 0.000007781939 |
| m243_a1000 | -0.000007425001 | 0.000010445474 |

The result preserves the M244 diagnosis: M243 improves the M223 source while
regressing the protected-key source.

## Tests

Focused evaluator tests:

```text
6 passed
```

The new tests cover:

- source spec parsing;
- exact row matching;
- clamped source denominators when weights sum below `1.0`;
- strict rejection when a combined row has no source match.

## Decision

M245 is complete as infrastructure. It does not promote a driver checkpoint.

Next repair should use this evaluator as a lexicographic gate:

```text
protected_key source delta <= 0
M223 source delta < 0
aggregate M232 delta <= 0
```

Next step:

```text
m246-source-balanced-outcome-loss-design
```
