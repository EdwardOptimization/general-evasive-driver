# M244 M243 Protected-Key Objective Conflict Audit

M244 audits the M243 exact-objective conflict before any additional PPO. The
audit uses the same full-corpus objective formula as `weighted_mean`: because
the combined M232 row weights sum to `0.357483016327`, the denominator is
clamped to `1.0`.

Actor inputs are unchanged. No PPO was run.

## Setup

Current public-gate base:

```text
runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
```

M243 interpolation policies:

```text
runs/m243_m239_to_raw_interpolation/checkpoints/alpha_0_1.pt
runs/m243_m239_to_raw_interpolation/checkpoints/alpha_0_25.pt
runs/m243_m239_to_raw_interpolation/checkpoints/alpha_0_5.pt
runs/m243_m239_to_raw_interpolation/checkpoints/alpha_0_75.pt
runs/m243_m239_to_raw_interpolation/checkpoints/alpha_1.pt
```

Audited corpora:

```text
runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz
runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz
runs/m231_protected_key_snippet_surface/protected_key_snippets.npz
```

Output artifacts:

```text
runs/m244_m243_protected_key_objective_conflict_audit/summary.json
runs/m244_m243_protected_key_objective_conflict_audit/policy_exact_objective_summary.csv
runs/m244_m243_protected_key_objective_conflict_audit/source_exact_objective_summary.csv
runs/m244_m243_protected_key_objective_conflict_audit/source_delta_decomposition.csv
runs/m244_m243_protected_key_objective_conflict_audit/per_row_exact_objective.csv
```

## Exact Loss Reproduction

The corrected audit reproduces the M243 exact M232 losses with maximum absolute
error `4.689e-13`, so the source decomposition uses the same objective as the
promotion gate.

| Policy | Exact M232 loss |
| --- | ---: |
| m239_a500 | 0.244649454951 |
| m243_a100 | 0.244649633765 |
| m243_a250 | 0.244650021195 |
| m243_a500 | 0.244650721550 |
| m243_a750 | 0.244651511312 |
| m243_a1000 | 0.244652479887 |

## Source Decomposition

The combined M232 corpus contains 17 M223 rows and 1 protected-key row. M243
improves the M223 component, but the protected-key component worsens enough to
dominate the aggregate M232 movement.

| Policy | M223 delta | Protected-key delta | Reconstructed M232 delta |
| --- | ---: | ---: | ---: |
| m243_a100 | -0.000000821309 | 0.000001015703 | 0.000000194394 |
| m243_a250 | -0.000001983192 | 0.000002556134 | 0.000000572942 |
| m243_a500 | -0.000003888495 | 0.000005152159 | 0.000001263664 |
| m243_a750 | -0.000005702850 | 0.000007781939 | 0.000002079090 |
| m243_a1000 | -0.000007425001 | 0.000010445474 | 0.000003020473 |

This is a clean objective conflict:

- M243 is not broadly moving the old M223 surface in the wrong direction.
- M243 is over-optimizing M223 while sacrificing the protected-key row.
- M223-only improvement is not sufficient evidence for continuation.

## Decision

M243 remains rejected. M239 alpha `0.5` remains the current public-gate base.

M244 classifies the M243 failure as:

```text
objective_overfit
promotion_gate_failure
```

The next repair should make exact objective reporting source-aware and
lexicographic: a candidate must not regress the protected-key source component
while improving the broader M223 component and aggregate M232 objective.

Next step:

```text
m245-source-aware-exact-objective-evaluator
```
