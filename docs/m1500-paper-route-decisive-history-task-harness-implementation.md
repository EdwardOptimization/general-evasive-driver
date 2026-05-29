# M1500 Paper-Route Decisive History Task Harness Implementation

## Summary

M1500 implements no-training T4/T5 decisive-history task harness scaffolding.

Decision:

```text
decisive_history_task_harness_implemented_admit_candidate_generation_design
```

This milestone does not train, run PPO, run replay, promote, use private
holdout, export corpus, change actor inputs, or claim task success,
paper-level evidence, recurrent-belief advantage, or level3 self-identification.

## Implementation

Added:

```text
src/autodrift/decisive_history_tasks.py
tests/test_decisive_history_tasks.py
```

The module provides metadata-only harness support:

```text
DecisiveHistoryTaskCandidate
DecisiveHistoryThresholds
CandidateClassification
validate_candidate
classify_candidate
source_diversity_summary
matching_diagnostics_summary
build_harness_summary
run_harness_smoke
```

It intentionally does not import the simulator, trainer, policy, replay gates,
or checkpoints. It only validates task-candidate metadata and writes
no-training smoke artifacts.

## Task Families

Supported task families:

```text
T4: same-current same-recent-window different-older-history
T5: terminal-boundary near-constraint avoidance
```

Supported intervention labels:

```text
normal
current_tiled
reset
delayed
wrong_history
zero_response
zero_action_history
```

The decisive T4 acceptance path requires matched current/recent evidence,
different older history, action divergence, and wrong-history outcome relevance.

The decisive T5 acceptance path requires near-boundary normal margin and an
outcome-relevant history intervention gap or success drop.

## Focused Tests

Command:

```bash
PYTHONPATH=src python -m pytest tests/test_decisive_history_tasks.py -q
```

Result:

```text
6 passed in 0.14s
```

Covered behavior:

```text
T4 accepts same-current/different-older-history candidates with wrong-history
outcome gap;
T4 rejects current mismatch and actor-label shortcuts;
T5 accepts near-boundary success-drop candidates;
T5 rejects non-near-boundary candidates;
matching and source-diversity summaries are deterministic;
runtime smoke writes summary and candidate CSV without training or replay.
```

## Runtime Smoke

Command:

```bash
PYTHONPATH=src python -m autodrift.decisive_history_tasks \
  --run-dir runs/m1500_decisive_history_task_harness_smoke
```

Output:

```text
summary=runs/m1500_decisive_history_task_harness_smoke/summary.json
candidate_count=3
accepted_count=2
```

Smoke summary:

```text
result_class: decisive_history_task_harness_summary
candidate_count: 3
accepted_count: 2
accepted_t4_count: 1
accepted_t5_count: 1
validation_error_count: 1
validation_reasons: current_distance_too_large = 1
unique_seeds: 3
unique_capability_pairs: 3
unique_geometry_keys: 3
unique_source_keys: 3
max_source_share: 0.3333333333333333
training_started: false
evaluation_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

The rejected candidate is intentional; it proves the current-distance matching
diagnostic is active.

## Guardrails

```text
training_started: false
evaluation_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next Route

Route to:

```text
m1501-paper-route-decisive-history-candidate-generation-design
```

M1501 should design how to connect the metadata harness to current-sim public
candidate generation. It should still be no-training and should not run replay
or PPO.
