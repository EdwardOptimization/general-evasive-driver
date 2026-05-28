# M1304 Paper-Route Source-History Repeat Failed-Offset Audit

## Summary

M1304 implements and runs a no-training audit for the failed offsets from M1302.

Decision:

```text
source_history_failed_offset_audit_concentrated_route_to_refresh_design
```

The failed offsets are not just random pair singletons. The failure groups are
concentrated by probe template and source fault family:

```text
top_failed_probe_template: left_brake_probe
top_failed_probe_template_share: 0.6086956522

top_failed_source_family_pair: single_wheel_grip_collapse->single_wheel_grip_collapse
top_failed_source_family_pair_share: 0.5652173913

top_failed_source_fault_pair: rear_left_grip_collapse->rear_right_grip_collapse
top_failed_source_fault_pair_share: 0.5652173913
```

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
threshold relaxation, high-fidelity validation claim, paper-level claim, or
self-identification claim occurs in M1304.

## Command

Focused test:

```bash
PYTHONPATH=src python -m pytest -q \
  tests/test_source_history_repeat_failed_offset_audit.py
```

Result:

```text
1 passed
```

Audit:

```bash
PYTHONPATH=src python -m autodrift.source_history_repeat_failed_offset_audit \
  --repeat-run-dir runs/m1302_source_history_trainable_scope_repeat_probe \
  --history-run-dir runs/m1280_four_wheel_source_response_history_materialization \
  --run-dir runs/m1304_source_history_repeat_failed_offset_audit
```

## Implementation

Added:

```text
src/autodrift/source_history_repeat_failed_offset_audit.py
tests/test_source_history_repeat_failed_offset_audit.py
```

The audit reads existing M1302 and M1280 artifacts only. It writes:

```text
runs/m1304_source_history_repeat_failed_offset_audit/summary.json
runs/m1304_source_history_repeat_failed_offset_audit/offset_summary.csv
runs/m1304_source_history_repeat_failed_offset_audit/eval_directional_rows.csv
runs/m1304_source_history_repeat_failed_offset_audit/eval_group_rows.csv
runs/m1304_source_history_repeat_failed_offset_audit/failed_eval_groups.csv
runs/m1304_source_history_repeat_failed_offset_audit/composition_summary.csv
```

## Result

Offset summary:

```text
passing_offsets: 0|1|3
failing_offsets: 2|4
passing_offset_count: 3
failing_offset_count: 2
eval_directional_row_count: 152
eval_group_count: 76
failed_eval_group_count: 23
failed_eval_group_fraction: 0.3026315789
```

Failed group margin summary:

```text
failed_eval_group_min_margin_mean: -0.5459670399
failed_eval_group_min_margin_min: -1.9593467712
failed_eval_group_min_margin_max: -0.0005912781
```

Offset-level details:

```text
offset 0: pass, eval failed group fraction 0.7500, eval source family pairs 3
offset 1: pass, eval failed group fraction 0.7222, eval source family pairs 3
offset 2: fail, eval failed group fraction 0.8125, eval source family pairs 2
offset 3: pass, eval failed group fraction 0.7143, eval source family pairs 2
offset 4: fail, eval failed group fraction 0.8333, eval source family pairs 2
```

Concentration summary:

```text
top_failed_pair_id: 124
top_failed_pair_id_share: 0.0869565217

top_failed_probe_template: left_brake_probe
top_failed_probe_template_share: 0.6086956522

top_failed_source_family_pair: single_wheel_grip_collapse->single_wheel_grip_collapse
top_failed_source_family_pair_share: 0.5652173913

top_failed_source_fault_pair: rear_left_grip_collapse->rear_right_grip_collapse
top_failed_source_fault_pair_share: 0.5652173913
```

## Interpretation

Supported:

```text
The M1302 repeat failure is not caused by one pair ID. The top failed pair
accounts for only 2/23 failed eval groups.
```

Supported:

```text
The failed eval groups concentrate by `left_brake_probe` and by the
rear-left versus rear-right single-wheel grip collapse family.
```

Supported:

```text
The failure mode is compatible with corpus/objective imbalance. It is not yet
evidence that the `fusion_head` direction is invalid.
```

Not supported:

```text
Direct PPO admission.
```

Not supported:

```text
Threshold relaxation.
```

Not supported:

```text
Closed-loop driver performance or strong self-identification.
```

## Next Routing

Next:

```text
m1305-paper-route-source-history-concentration-aware-refresh-design
```

M1305 should design a concentration-aware refresh before any new trainable
probe. The design should decide whether to:

```text
rebalance eval/train pair partitions by source family and probe template;
add failed-offset source-family/template weights to the objective;
refresh the corpus with more non-singleton source-family coverage;
or synthesize/pivot if the branch is becoming fixed-public-row overfit.
```

The next step should remain no-training design. PPO and promotion remain
blocked.

## Guardrails

M1304 preserves:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
self_identification_claimed: false
```
