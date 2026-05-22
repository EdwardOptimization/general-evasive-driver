# M247 Source-Balanced Outcome Loss Implementation

M247 implements the source-balanced PPO auxiliary loss selected in M246. No PPO
was run and actor inputs are unchanged.

## Change

`PPOConfig` now accepts:

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

Each source is loaded independently and contributes:

```text
loss += source_coef * outcome_weighted_intervention_loss(source_npz)
```

The legacy combined `outcome_intervention_aux_coef` path remains available.

## Validation

The new config path rejects:

- non-list `outcome_intervention_source_losses`;
- missing source names;
- duplicate metric-normalized names;
- missing `snapshot_npz`;
- non-positive `coef`;
- non-positive `batch_size`;
- negative `logprob_margin`;
- use without online recurrent sequence training.

Per-source metrics are logged as:

```text
outcome_intervention_source_<name>_loss_mean
outcome_intervention_source_<name>_coef
```

## Tests

Focused tests:

```text
66 passed
```

The new tests verify:

- per-source loss metrics are present in `train_metrics.csv`;
- source names are normalized for metric columns;
- duplicate source names are rejected;
- existing combined outcome intervention tests still pass.

## Decision

M247 is complete as infrastructure. It does not promote a driver checkpoint.

Next step:

```text
m248-source-balanced-ppo-smoke-from-m239
```
