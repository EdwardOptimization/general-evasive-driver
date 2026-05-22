# M270 Source-Balanced Multi-Surface Anchor Corpus

M270 builds a combined old+current+protected-key snippet anchor corpus after
M268 showed that an M267-only actor update can wash out older M183/M193 proof
surfaces.

No PPO, actor update, promotion, or actor-input change was performed.

## Inputs

| Source | Rows | Artifact |
| --- | ---: | --- |
| M183 M168 | 16 | `runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz` |
| M183 M170 | 17 | `runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz` |
| M193 M189 | 14 | `runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.npz` |
| M212 M204 | 17 | `runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.npz` |
| M223 M219 | 17 | `runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz` |
| M267 M264 | 17 | `runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.npz` |
| Protected key `9944` | 1 | `runs/m231_protected_key_snippet_surface/outcome_intervention_snippets.npz` |

## Source Balance

M270 rescales row weights so each source surface contributes total weight `1.0`.
This keeps old surfaces and the protected-key diagnostic from being hidden by
aggregate row counts.

| Source | Rows | Balanced weight sum | Min row weight | Max row weight |
| --- | ---: | ---: | ---: | ---: |
| M183 M168 | 16 | 1.0 | 0.042779 | 0.082737 |
| M183 M170 | 17 | 1.0 | 0.037098 | 0.079566 |
| M193 M189 | 14 | 1.0 | 0.043167 | 0.099155 |
| M212 M204 | 17 | 1.0 | 0.037197 | 0.080638 |
| M223 M219 | 17 | 1.0 | 0.037341 | 0.080046 |
| M267 M264 | 17 | 1.0 | 0.037505 | 0.080193 |
| Protected key `9944` | 1 | 1.0 | 1.000000 | 1.000000 |

The protected key has one row, so its per-row weight is high. That is deliberate
source balancing, not row-count balancing. Later actor-update gates still must
prove that this does not damage broader replay behavior.

## Output

Artifacts:

```text
runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.csv
runs/m270_source_balanced_multi_surface_anchor/summary.json
runs/m270_source_balanced_multi_surface_anchor/validation.json
```

Validation:

| Array | Shape |
| --- | ---: |
| `observation` | `99 x 72` |
| `preferred_hidden` | `99 x 128` |
| `rejected_hidden` | `99 x 128` |
| `preferred_action` | `99 x 3` |
| `weight` | `99` |

| Metric | Value |
| --- | ---: |
| Output rows | 99 |
| Source count | 7 |
| Weight sum | 6.9999995 |
| Weight min | 0.037098 |
| Weight max | 1.000000 |
| Loader validation | true |

The combined NPZ loads successfully through
`load_outcome_intervention_snippets(obs_dim=72, hidden_size=128, act_dim=3)`.

## Decision

M270 is positive as infrastructure.

What it proves:

- one validated corpus can carry old M183/M193, recent M212/M223/M267, and the
  protected-key diagnostic at the same time;
- source-level weights are explicit instead of aggregate-dominated;
- the combined corpus is compatible with the existing outcome/snippet anchor
  loader.

What it does not prove:

- that an actor update using this corpus is safe;
- that the high per-row protected-key weight is harmless;
- that PPO can continue.

Decision:

```text
admit_multi_surface_guarded_actor_update
```

Next step:

```text
m271-m270-multi-surface-guarded-actor-update
```

M271 may run exactly one small guarded actor update from `m264_a001` using the
M270 combined corpus. It must gate fixed combined objective first, then old and
current replay surfaces, protected-key diagnostic, and behavior seeds before any
repeat or PPO.
