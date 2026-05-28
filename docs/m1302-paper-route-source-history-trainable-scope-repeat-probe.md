# M1302 Paper-Route Source-History Trainable-Scope Repeat Probe

## Summary

M1302 implements and runs the split-repeat robustness probe designed in M1301.

Decision:

```text
source_history_trainable_scope_repeat_mixed_route_to_result_audit
```

Result class:

```text
source_history_trainable_scope_repeat_mixed
```

The M1299 `fusion_head` signal is real but split-sensitive. It passes `3/5`
deterministic pair-disjoint split offsets, but does not meet the repeat-strong
mean eval threshold.

No PPO, checkpoint promotion, private holdout, actor-input expansion, threshold
relaxation, high-fidelity validation claim, paper-level claim, or
self-identification claim occurs in M1302.

## Command

Focused test:

```bash
PYTHONPATH=src python -m pytest -q \
  tests/test_source_history_trainable_scope_probe.py
```

Result:

```text
1 passed in 1.62s
```

Probe:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_history_trainable_scope_probe \
  --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --history-run-dir runs/m1280_four_wheel_source_response_history_materialization \
  --intervention-run-dir runs/m1277_four_wheel_source_intervention_materialization \
  --run-dir runs/m1302_source_history_trainable_scope_repeat_probe \
  --device cpu \
  --steps 400 \
  --lr 0.0002 \
  --target-margin 0.05 \
  --scopes fusion_head \
  --split-offsets 0,1,2,3,4
```

## Implementation

Updated:

```text
src/autodrift/source_history_trainable_scope_probe.py
tests/test_source_history_trainable_scope_probe.py
```

The implementation adds:

```text
split_mod / split_offsets CLI support;
repeat_summaries.csv;
per-offset checkpoint names;
per-offset split rows, directional rows, group rows, and parameter deltas;
repeat-level result classification.
```

## Result

Repeat summary:

```text
scope: fusion_head
offset_count: 5
offset_pass_count: 3
required_pass_count: 3
mean_eval_both_directional_fraction: 0.2335317460
mean_eval_group_all_rows_both_positive_fraction: 0.2335317460
mean_full_both_positive_count: 38.0
mean_full_group_all_rows_both_positive_count: 19.0
min_eval_both_directional_fraction: 0.1666666667
min_eval_group_all_rows_both_positive_fraction: 0.1666666667
repeat_class: trainable_scope_repeat_mixed
```

Why mixed:

```text
offset_pass_count reaches 3/5,
but mean eval row/group fractions are 0.2335317460 < 0.25.
```

Best offset:

```text
best_split_offset: 3
best_eval_both_directional_fraction: 0.2857142857
best_eval_group_all_rows_both_positive_fraction: 0.2857142857
best_full_both_positive_count: 40
best_full_group_all_rows_both_positive_count: 20
```

Per-offset outcome:

```text
offset 0: pass, eval row/group 0.25, full 46/152 rows and 23/76 groups
offset 1: pass, eval row/group 0.2777777778, full 48/152 rows and 24/76 groups
offset 2: fail, eval row/group 0.1875, full 32/152 rows and 16/76 groups
offset 3: pass, eval row/group 0.2857142857, full 40/152 rows and 20/76 groups
offset 4: fail, eval row/group 0.1666666667, full 24/152 rows and 12/76 groups
```

Mutation guard:

```text
forbidden_parameter_mutation_detected: false
```

All offsets changed only allowed groups for `fusion_head`:

```text
actor_mean
response_context_fusion
```

## Interpretation

Supported:

```text
The M1299 fusion_head signal is not a single-offset artifact. Three of five
pair-disjoint split offsets pass the per-offset threshold.
```

Supported:

```text
The signal is split-sensitive. Two offsets fail, and mean eval row/group
fractions do not meet the repeat-strong threshold.
```

Supported:

```text
The mutation guard remains clean across all offsets.
```

Not supported:

```text
Repeat-robust trainable-scope result.
```

Not supported:

```text
PPO admission or checkpoint promotion.
```

Not supported:

```text
Closed-loop driver performance or self-identification proof.
```

## Guardrails

M1302 preserved:

```text
labels_enter_actor_input: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
forbidden_parameter_mutation_detected: false
```

## Next Step

Pre-register:

```text
m1303-paper-route-source-history-trainable-scope-repeat-result-audit
```

M1303 should decide whether to:

```text
1. tune the trainable-scope objective and repeat;
2. inspect failed offsets for corpus/source imbalance;
3. refresh the source-history corpus;
4. move toward sequence/trajectory preference targets.
```

PPO and promotion remain blocked.
