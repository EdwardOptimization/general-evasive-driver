# M1502 Paper-Route Decisive History Candidate Planner Implementation

## Summary

M1502 implements a metadata-only source-plan planner for T4/T5 decisive-history
candidates.

Decision:

```text
decisive_history_candidate_planner_implemented_admit_public_planner_smoke
```

This milestone does not run simulator replay, train, run PPO, promote, use
private holdout, export a corpus, change actor inputs, or claim candidate
existence beyond deterministic planner smoke.

## Implementation

Added:

```text
src/autodrift/decisive_history_candidate_planner.py
tests/test_decisive_history_candidate_planner.py
```

The planner provides:

```text
CandidateSourcePlan
CandidatePlannerConfig
default_source_plans
validate_source_plan
generate_candidates_from_plan
generate_candidates
build_planner_summary
run_candidate_planner_smoke
```

It depends on the M1500 metadata harness:

```text
DecisiveHistoryTaskCandidate
classify_candidate
candidate_to_row
build_harness_summary
```

It intentionally does not import `env`, policy code, trainer code, replay
gates, or checkpoints.

## Source Plan Coverage

The deterministic default plan covers the M1501 source families:

```text
t4_staged_warmup_capability
t4_capability_step_temporal
t4_actuator_delay_response
t5_near_boundary_warmup
t5_high_speed_close_obstacle
t5_boundary_axis_retarget
```

It preserves separate public seed namespaces and emits M1500-compatible
candidate rows with:

```text
task_family
candidate_id
seed
capability_pair
reveal_step
decision_step
geometry_key
current_distance
recent_window_distance
older_history_distance
normal_margin
action_divergence
intervention_margins
labels_enter_actor_input
```

## Focused Tests

Command:

```bash
PYTHONPATH=src python -m pytest tests/test_decisive_history_candidate_planner.py -q
```

Result:

```text
5 passed in 0.08s
```

Covered behavior:

```text
default source plans cover T4 and T5 public families;
source-plan validation rejects shortcut labels and malformed plans;
candidate generation emits M1500-compatible rows;
invalid task families fail before smoke;
planner smoke writes summary, source plans, family summary, and candidate rows
without training, replay, PPO, promotion, private holdout, corpus export, or
actor-input changes.
```

## Runtime Smoke

Command:

```bash
PYTHONPATH=src python -m autodrift.decisive_history_candidate_planner \
  --run-dir runs/m1502_decisive_history_candidate_planner_smoke \
  --seed-count 2
```

Output:

```text
summary=runs/m1502_decisive_history_candidate_planner_smoke/summary.json
generated_candidate_rows=12
accepted_count=12
```

Smoke summary:

```text
result_class: decisive_history_candidate_planner_summary
source_plan_count: 6
generated_candidate_rows: 12
harness.accepted_count: 12
harness.accepted_t4_count: 6
harness.accepted_t5_count: 6
harness.validation_error_count: 0
harness.source_diversity.unique_seeds: 12
harness.source_diversity.unique_capability_pairs: 8
harness.source_diversity.unique_geometry_keys: 12
harness.source_diversity.unique_reveal_steps: 12
harness.source_diversity.max_source_share: 0.08333333333333333
labels_enter_actor_input: false
private_holdout_used: false
actor_input_contract_changed: false
training_started: false
evaluation_started: false
replay_started: false
ppo_used: false
promoted: false
training_corpus_exported: false
level3_self_id_claim_made: false
```

Artifacts:

```text
runs/m1502_decisive_history_candidate_planner_smoke/source_plan_rows.csv
runs/m1502_decisive_history_candidate_planner_smoke/candidate_rows.csv
runs/m1502_decisive_history_candidate_planner_smoke/source_family_summary.csv
runs/m1502_decisive_history_candidate_planner_smoke/summary.json
```

## Interpretation

M1502 proves only that the source-plan layer can produce M1500-compatible
candidate metadata under no-training guardrails. It does not prove that
current-sim rollouts can produce real T4/T5 decisive candidates.

The next milestone should run a larger public no-training planner smoke against
the M1501 smoke thresholds before any simulator replay or controller training.

## Guardrails

```text
simulator_replay_started: false
training_started: false
evaluation_started: false
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
m1503-paper-route-decisive-history-public-planner-smoke
```

M1503 should run the no-training planner at public-smoke scale and audit the
M1501 thresholds. It should still not run simulator replay, PPO, or training.
