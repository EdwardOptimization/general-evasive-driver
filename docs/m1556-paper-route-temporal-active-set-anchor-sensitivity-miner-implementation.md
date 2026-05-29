# M1556 Paper-Route Temporal Active-Set Anchor-Sensitivity Miner Implementation

## Summary

M1556 implements the no-training temporal active-set miner designed in M1555.
It replays the fixed P0 human-view online-GRU actor to bounded temporal anchors
and applies one-step local action overrides before continuing the same fixed
policy.

Final decision:

```text
temporal_active_set_miner_smoke_sparse_active_set_route_to_audit
```

The implementation and artifacts are clean, but the corrected active-set gates
fail. The miner found only `2` valid action-sensitive anchors after filtering
failed-anchor NaN artifacts, both from `curved_boundary_obstacle` at the
`reveal` window. This is not enough to justify a history-intervention replay.

## Implementation

Added:

```text
src/autodrift/temporal_active_set_anchor_sensitivity_miner.py
tests/test_temporal_active_set_anchor_sensitivity_miner.py
```

The miner writes:

```text
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/source_spec_rows.csv
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/anchor_candidate_rows.csv
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/local_perturbation_rows.csv
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/accepted_active_anchor_rows.csv
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/source_family_summary.csv
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/window_summary.csv
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/guardrail_summary.csv
runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke/summary.json
```

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_temporal_active_set_anchor_sensitivity_miner.py -q
4 passed
```

Smoke command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.temporal_active_set_anchor_sensitivity_miner \
  --output-dir runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke \
  --seed 1843 \
  --seed-count 3 \
  --max-base-rows 24 \
  --max-calibration-specs 240 \
  --max-anchors 96
```

## Correctness Fix During Implementation

The first smoke exposed a metric artifact: failed anchor replays produced NaN
terminal margins, and NaN gaps could be counted as active anchors. This was
fixed before the final result:

```text
active anchors now require normal_replay_status == ok;
local rows must have replay_status == ok;
non-finite margin gaps are treated as zero;
duplicate calibration_id@anchor_step windows are de-duplicated.
```

The final numbers below are from the corrected run.

## Final Result

```text
anchor_candidate_count: 96
local_perturbation_row_count: 576
action_sensitive_anchor_count: 2
predecision_sensitive_anchor_count: 2
source_family_count: 5
max_single_family_share: 0.20833333333333334
active_source_family_count: 1
max_single_active_family_share: 1.0
active_anchor_window_count: 1
success_flip_count: 4
collision_flip_count: 0
max_abs_terminal_margin_gap: 0.010894415363880583
anchor_replay_failure_count: 20
local_perturbation_failure_count: 120
passes_public_smoke_gates: false
passes_evidence_quality_targets: false
guardrail_violation_count: 0
```

Active anchors:

```text
source_family: curved_boundary_obstacle
anchor_window: reveal
active_anchor_count: 2
```

Window summary:

```text
reveal: 2 active / 20 candidate
reveal_plus_4: 0 active / 20 candidate
decision_minus_16: 0 active / 20 candidate
decision_minus_8: 0 active / 0 candidate after de-duplication
decision: 0 active / 20 candidate
post_decision_8: 0 active / 16 candidate
```

## Interpretation

M1556 confirms that the no-training miner works, but it does not find a
source-diverse temporal active set under the current M1550/M1555 source
construction.

The result is a useful negative result:

```text
pair-expanded anchors are not merely too few;
even temporal local-action sensitivity remains sparse and source-concentrated.
```

The `success_flip_count` is `4`, but no collision flips occur and the maximum
terminal-margin gap is below the pre-registered `0.02` threshold. The flips are
not enough to support materialization or self-identification claims because they
are concentrated in one source family and one temporal window.

## Guardrails

```text
history_interventions_executed: false
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1557-paper-route-temporal-active-set-anchor-sensitivity-miner-result-audit
```

M1557 must audit whether this is primarily scenario/source sampling failure,
local perturbation design weakness, or a branch-level stop condition. History
interventions remain blocked until that audit.
