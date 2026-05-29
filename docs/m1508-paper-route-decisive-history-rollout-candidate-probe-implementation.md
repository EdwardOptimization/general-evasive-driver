# M1508 Paper-Route Decisive History Rollout Candidate Probe Implementation

## Summary

M1508 implements no-training rollout candidate scaffolding: schemas, distance
helpers, materialization guards, synthetic focused tests, and a synthetic smoke.

Decision:

```text
decisive_history_rollout_candidate_scaffold_implemented_admit_branch_synthesis
```

This milestone does not run real rollout candidate generation, fixed-policy
runner integration, replay, PPO, training, promotion, private holdout, corpus
export, actor-input changes, or level3 self-ID claims.

## Implementation

Added:

```text
src/autodrift/decisive_history_rollout_candidates.py
tests/test_decisive_history_rollout_candidates.py
```

The module provides:

```text
RolloutCandidateMeasurement
CandidateMaterializationResult
normalized_l2
current_frame_distance
history_window_distance
action_sequence_divergence
materialize_candidate
materialize_measurements
build_rollout_candidate_summary
run_rollout_candidate_scaffold_smoke
```

It uses the M1500 `DecisiveHistoryTaskCandidate` harness for candidate
classification once measurements are declared rollout-measured.

## Materialization Guard

Candidate rows may only materialize when:

```text
measured_from_rollout == true
reset_only_source == false
labels_enter_actor_input == false
M1500/M1501 candidate classification accepts the row
```

This explicitly prevents reset-only runtime evidence from becoming candidate
evidence.

## Focused Tests

Command:

```bash
PYTHONPATH=src python -m pytest tests/test_decisive_history_rollout_candidates.py -q
```

Result:

```text
5 passed in 0.09s
```

Covered behavior:

```text
distance helpers are normalized and shape-checked;
measured T4 rows can materialize;
reset-only sources are rejected;
actor-input label leakage is rejected;
synthetic smoke writes guarded artifacts and M1500-compatible candidates.
```

## Synthetic Smoke

Command:

```bash
PYTHONPATH=src python -m autodrift.decisive_history_rollout_candidates \
  --run-dir runs/m1508_decisive_history_rollout_candidate_scaffold_smoke
```

Output:

```text
summary=runs/m1508_decisive_history_rollout_candidate_scaffold_smoke/summary.json
materialized_candidate_count=2
rejected_count=1
```

Summary:

```text
result_class: decisive_history_rollout_candidate_scaffold_smoke
measurement_count: 3
materialized_candidate_count: 2
rejected_count: 1
accepted_t4_count: 1
accepted_t5_count: 1
candidate_materialized_from_reset_only: false
labels_enter_actor_input: false
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
level3_self_id_claim_made: false
```

Rejected reasons:

```text
not_measured_from_rollout: 1
reset_only_source: 1
```

Harness summary over materialized synthetic candidates:

```text
accepted_count: 2
accepted_t4_count: 1
accepted_t5_count: 1
validation_error_count: 0
```

## Interpretation

M1508 is scaffolding only. It proves that measured rows can be converted to
M1500-compatible candidates and that reset-only rows are blocked. It does not
run a fixed-policy source rollout, collect real trace windows, perform
interventions, or prove that current-sim can produce real T4/T5 candidates.

The next milestone should synthesize the M1499-M1508 decisive-history task
matrix branch before any bounded fixed-policy runner design. The branch has
reached the workflow synthesis cadence, and reset-only/synthetic evidence must
remain separated from real rollout candidate evidence.

## Artifacts

```text
runs/m1508_decisive_history_rollout_candidate_scaffold_smoke/measurement_rows.csv
runs/m1508_decisive_history_rollout_candidate_scaffold_smoke/materialized_candidate_rows.csv
runs/m1508_decisive_history_rollout_candidate_scaffold_smoke/summary.json
```

## Next Route

Route to:

```text
m1509-paper-route-decisive-history-task-matrix-synthesis
```
