# M1306 Paper-Route Source-History Concentration Refresh Plan

## Summary

M1306 implements and runs the no-training concentration-aware refresh plan
designed in M1305.

Decision:

```text
source_history_concentration_refresh_plan_admissible_route_to_weighted_repeat_design
```

The plan is admissible as infrastructure. It creates pair-disjoint balanced
folds and capped group-level weights without using pair-specific weights.

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
threshold relaxation, high-fidelity validation claim, paper-level claim, or
self-identification claim occurs in M1306.

## Command

Focused test:

```bash
PYTHONPATH=src python -m pytest -q \
  tests/test_source_history_concentration_refresh_plan.py
```

Result:

```text
1 passed
```

Plan builder:

```bash
PYTHONPATH=src python -m autodrift.source_history_concentration_refresh_plan \
  --failed-offset-run-dir runs/m1304_source_history_repeat_failed_offset_audit \
  --run-dir runs/m1306_source_history_concentration_refresh_plan
```

## Implementation

Added:

```text
src/autodrift/source_history_concentration_refresh_plan.py
tests/test_source_history_concentration_refresh_plan.py
```

The plan builder reads M1304 group artifacts and writes:

```text
runs/m1306_source_history_concentration_refresh_plan/summary.json
runs/m1306_source_history_concentration_refresh_plan/balanced_split_rows.csv
runs/m1306_source_history_concentration_refresh_plan/group_weight_rows.csv
runs/m1306_source_history_concentration_refresh_plan/fold_composition_summary.csv
runs/m1306_source_history_concentration_refresh_plan/original_fold_composition_summary.csv
```

## Result

Core plan metrics:

```text
result_class: source_history_concentration_refresh_plan_admissible
group_count: 76
pair_count: 38
fold_count: 5
pair_disjoint: true
all_folds_nonempty: true
all_folds_have_both_probe_templates: true
pair_specific_weight_used: false
```

Weight metrics:

```text
min_group_weight: 1.0151828847
max_group_weight: 2.0000000000
mean_group_weight: 1.2514206712
weight_cap: 2.0000000000
```

Composition metrics:

```text
original_max_source_family_pair_fold_share: 0.6666666667
balanced_max_source_family_pair_fold_share: 0.6250000000
original_max_probe_template_fold_share: 0.5000000000
balanced_max_probe_template_fold_share: 0.5000000000
composition_improved: true
source_family_pair_count: 3
dominant_source_family_pair: single_wheel_grip_collapse->single_wheel_grip_collapse
dominant_source_family_pair_share: 0.5526315789
```

## Interpretation

Supported:

```text
The plan can rebalance the public folds without violating pair disjointness.
```

Supported:

```text
The plan does not use pair-specific weights. The next weighted repeat would be
source-family/probe-template/margin-bucket based rather than pair-id based.
```

Supported:

```text
The dominant source-family fold share improves from 0.6667 to 0.6250.
```

Not supported:

```text
The weighted objective will improve the trainable-scope repeat.
```

Not supported:

```text
Closed-loop driver performance or strong self-identification.
```

## Caveats

The corpus is still small and source-family dominated:

```text
single_wheel_grip_collapse->single_wheel_grip_collapse share: 0.5526315789
```

The plan is therefore admissible but not a guarantee. It should feed a bounded
weighted repeat design, not an immediate PPO continuation.

The max weight hits the pre-registered cap:

```text
max_group_weight: 2.0
```

That is allowed, but the next implementation should monitor whether capped
groups dominate the gradient.

## Next Routing

Next:

```text
m1307-paper-route-source-history-weighted-repeat-design
```

M1307 should design how to use:

```text
balanced_split_rows.csv
group_weight_rows.csv
```

in a bounded no-PPO weighted `fusion_head` repeat. It should define exact
pass/fail criteria and keep PPO blocked.

Because the trainable-scope escalation branch is near the workflow synthesis
cadence, M1307 should also require the following milestone to synthesize the
branch before any larger training or PPO step.

## Guardrails

M1306 preserves:

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
