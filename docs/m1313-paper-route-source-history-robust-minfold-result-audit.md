# M1313 Paper-Route Source-History Robust Min-Fold Result Audit

## Summary

M1313 audits M1312 before any further implementation.

Decision:

```text
robust_minfold_result_audit_pivot_to_source_history_corpus_expansion
```

M1312 is a meaningful improvement over M1309 weighted mean, but it is not
admissible. It improves aggregate repeat metrics and the top failed combo while
losing baseline passing offsets `0|1`. That is pass-surface swapping, not robust
repeat evidence.

The next step should not be another scalar-loss tweak. It should pivot to
source-history corpus expansion: more source pairs, more fault families, more
onset/timing variation, and more extreme but physically plausible response
histories before another policy-side objective run.

## Evidence

M1312 probe:

```text
result_class: source_history_trainable_scope_repeat_strong
best_repeat_offset_pass_count: 3
best_repeat_mean_eval_both_directional_fraction: 0.2517857143
best_repeat_mean_full_both_positive_count: 40.8
top_failed_combo_positive_delta: +6
baseline_pass_offsets: 0|1|3
current_pass_offsets: 2|3|4
baseline_pass_lost_offsets: 0|1
```

M1312 tradeoff audit:

```text
result_class: weighted_repeat_tradeoff_nonregressive
new_pass_offsets: 2|4
lost_pass_offsets: 0|1
mean_eval_both_directional_fraction_delta: +0.0182539683
mean_full_both_positive_count_delta: +2.8
full_baseline_positive_count: 95
full_weighted_positive_count: 102
full_improved_to_positive_count: 33
full_regressed_from_positive_count: 26
full_mean_margin_delta: +0.0183538462
top_failed_combo_positive_delta: +6
top_failed_combo_mean_margin_delta: +0.0019678615
```

## Supported Claims

Supported:

```text
The M1311 robust objective is directionally better than the M1309 weighted mean.
```

Evidence:

```text
M1309: repeat pass count 1/5, mean eval 0.2089285714, top combo +3
M1312: repeat pass count 3/5, mean eval 0.2517857143, top combo +6
```

Supported:

```text
The source-history signal is not exhausted; stronger objectives can move the
correct-history / wrong-history diagnostic in useful directions.
```

Supported:

```text
The current fixed source-history surface is too small or too brittle for
objective-only tuning to be accepted as robust evidence.
```

Evidence:

```text
M1312 achieves aggregate repeat-strong while swapping pass offsets from 0|1|3
to 2|3|4.
```

## Falsified Claims

Falsified:

```text
Train-split-only retention can guarantee no lost baseline pass offsets on the
current corpus.
```

Falsified:

```text
Aggregate repeat-strong classification is enough to admit PPO or promotion.
```

Falsified:

```text
The next step should be more scalar weight pressure on the same 76 public
groups.
```

## Root Cause

The current source-history corpus has:

```text
38 source pairs
76 pair/probe groups
5 deterministic folds
public fixed-current diagnostic rows only
```

With this scale, the objective can satisfy one subset by sacrificing another.
M1309 sacrificed global repeat for one strong split. M1312 recovered aggregate
repeat but sacrificed previously passing offsets. This is a classic
public-surface overfit / active-set swapping pattern.

The train-split-only rule also matters: held-out eval rows are intentionally not
trained on. Therefore retention losses built only from train groups cannot
guarantee retention on the held-out fold. That is correct protocol behavior, not
an implementation bug.

## Failure Taxonomy

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
The current source-history corpus is too narrow for repeat-robust objective
evidence; folds are small enough that useful directions swap pass surfaces.
```

Secondary:

```text
objective_overfit
```

Reason:

```text
The objective improves aggregate public diagnostics while losing baseline
passing offsets.
```

Not observed:

```text
contract_violation
forbidden_parameter_mutation
pair_specific_weighting
private_holdout_contamination
promotion_gate_failure
training_instability
```

## Decision

Next branch:

```text
paper_route_source_history_corpus_expansion
```

Next milestone:

```text
m1314-paper-route-source-history-corpus-expansion-design
```

The next design should expand the source-history substrate rather than tuning
the current one. The expansion should target:

- more source pairs per fault family;
- single-wheel grip collapse at all corners;
- transient grip loss and sudden friction patches;
- brake pull / stuck caliper / partial brake failure;
- drive torque loss / halfshaft-like failure;
- tire blowout-like drag/radius/friction change;
- split-mu and asymmetric road friction;
- onset timing variation;
- speed, curvature, obstacle timing, and road-boundary variation;
- enough pair-disjoint folds to reduce pass-surface swapping.

## Guardrails

Still blocked:

```text
PPO
promotion
private holdout
actor input changes
paper-level claims
closed-loop self-identification claims
```

Allowed next:

```text
design and build a larger source-history corpus before another policy-side
objective run.
```
