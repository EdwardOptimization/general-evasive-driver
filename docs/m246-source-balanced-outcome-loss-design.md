# M246 Source-Balanced Outcome Loss Design

M246 is a no-PPO design gate. It uses the M244/M245 source-aware evidence to
choose one bounded repair before any new training run.

Actor inputs are unchanged. No PPO was run.

## Problem

M243 used a single combined M232 outcome intervention corpus:

```text
outcome_intervention_snapshot_npz = runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz
outcome_intervention_aux_coef = 0.03
```

That combined corpus contains:

```text
17 M223 rows
1 protected-key row
```

M244/M245 showed the exact source movement:

| Policy | M223 delta | Protected-key delta |
| --- | ---: | ---: |
| m243_a100 | -0.000000821309 | 0.000001015703 |
| m243_a250 | -0.000001983192 | 0.000002556134 |
| m243_a500 | -0.000003888495 | 0.000005152159 |
| m243_a750 | -0.000005702850 | 0.000007781939 |
| m243_a1000 | -0.000007425001 | 0.000010445474 |

So the issue is not that M243 failed to improve the broad M223 surface. It
improved M223 while sacrificing the protected-key row.

## Diagnosis

The current PPO objective has source opacity:

- `outcome_weighted_intervention_loss` samples from the combined corpus.
- The protected-key row is one row among 18.
- Snippet and trajectory action anchors preserve action similarity, but M244
  measures the log-probability separation between preferred and wrong-history
  hidden states.
- Aggregate M232 can only say that some component moved; it cannot force the
  protected-key source to remain non-regressed during training.

Continuing with a combined-only outcome objective would likely keep producing
M223 improvement with protected-key drift.

## Rejected Repairs

Do not loosen the protected-key guard. The protected-key row exists because
prior PPO runs repeatedly left the normal-margin window.

Do not use M223-only improvement as a continuation criterion. M243 already
proved that is insufficient.

Do not merely increase the combined M232 coefficient. That still hides source
movement and can increase pressure on the 17-row M223 source without making the
protected-key source a first-class objective.

## Selected Repair

Implement a source-balanced outcome intervention loss:

```json
"outcome_intervention_source_losses": [
  {
    "name": "m223",
    "snapshot_npz": "runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz",
    "coef": 0.02,
    "batch_size": 17,
    "logprob_margin": 0.05
  },
  {
    "name": "protected_key",
    "snapshot_npz": "runs/m231_protected_key_snippet_surface/protected_key_snippets.npz",
    "coef": 0.08,
    "batch_size": 1,
    "logprob_margin": 0.05
  }
]
```

The config should allow multiple named source losses. Each source is loaded and
logged separately. For the next smoke, the combined M232 outcome loss should be
disabled or kept as reporting only; the active outcome pressure should come
from the named source losses.

The proposed coefficients intentionally give the one protected-key row a higher
separate coefficient without removing M223 pressure.

## Next PPO Gate

The next PPO candidate may only reach replay/protected-key/behavior gates after
passing the source-aware exact objective gate:

```text
protected_key delta <= +1e-8
M223 delta < 0
aggregate M232 delta <= +1e-8
```

Then it must still pass:

```text
M183 M168/M170 replay
M193 M189 replay
M212 M204 replay
M223 M219 replay
protected key 9944 guard
behavior seeds 9505/9506
```

## Decision

M246 selects source-balanced outcome intervention loss as the bounded repair.

Next step:

```text
m247-source-balanced-outcome-loss-implementation
```
