# M232 Protected-Key Combined Snippet Anchor Corpus

M232 builds one combined snippet/action-anchor corpus before any
protected-key-aware PPO repair. No PPO is run in this milestone.

Actor inputs are unchanged.

## Inputs

| Source | Rows | Artifact |
| --- | ---: | --- |
| M223 boundary proof surface | 17 | `runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz` |
| M231 protected key | 1 | `runs/m231_protected_key_snippet_surface/protected_key_snippets.npz` |

The protected key row is:

```text
9944|perturbed|28|28
```

## Output

Artifacts:

```text
runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz
runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.csv
runs/m232_combined_m223_m231_snippet_anchor/summary.json
runs/m232_combined_m223_m231_snippet_anchor/validation.json
```

The combined NPZ keeps the PPO snippet-action-anchor contract:

| Array | Shape | Notes |
| --- | ---: | --- |
| observation | 18 x 72 | human-view observation |
| preferred_hidden | 18 x 128 | deployable recurrent hidden |
| rejected_hidden | 18 x 128 | wrong-history hidden |
| preferred_action | 18 x 3 | M224 reference action |
| weight | 18 | positive finite weights |

Validation summary:

| Metric | Value |
| --- | ---: |
| M223 rows retained | 17 |
| M231 rows retained | 1 |
| output rows | 18 |
| protected key included | true |
| weight min | 0.011426 |
| weight max | 0.051482 |
| weight sum | 0.357483 |

The combined NPZ was loaded through:

```text
load_outcome_intervention_snippets(obs_dim=72, hidden_size=128, act_dim=3)
```

## Interpretation

M229 proved that anchoring only the M223 surface restores replay retention but
does not cover the historical protected key. M231 exported that missing key.
M232 now puts both surfaces into one corpus, so a later PPO smoke can protect
the replay surface and the protected key with the same snippet action anchor.

This milestone does not claim driver improvement.

## Decision

M232 completes as infrastructure.

Next blocker:

```text
m233-protected-key-aware-ppo-smoke-from-m224
```

M233 should run one bounded PPO smoke from M224 using the M232 combined corpus
for both outcome intervention and preferred-only snippet action anchoring, then
gate fixed objective, replay, behavior, and the protected key before any repeat.
