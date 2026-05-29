# M1506 Paper-Route Decisive History Env-Hook Runtime Smoke

## Summary

M1506 runs a reset-only current-sim runtime smoke for the M1505 env-hook specs.

Decision:

```text
decisive_history_env_hook_runtime_smoke_pass_admit_rollout_candidate_design
```

This milestone does not run policy replay, PPO, training, promotion, private
holdout, corpus export, actor-input changes, candidate materialization, or
level3 self-ID claims.

## Runtime Repair

The first reset-only probe exposed a real hook-config issue:

```text
Only t5_high_speed_close_obstacle reset successfully.
The other source families failed obstacle sampling because the metadata hook
kept the T5/T4 obstacle filters too narrow for reset viability.
```

M1506 repaired the hook config factory by broadening reset-smoke obstacle label
acceptance to:

```text
aeb_feasible
aes_feasible
drift_required
unavoidable
```

and by removing early `max_threshold_score` restrictions from the reset-smoke
hook configs. This is not a candidate-selection relaxation. Later rollout
candidate generation must still measure real terminal margins and filter
candidate rows under the M1500/M1501 thresholds.

## Implementation

Added:

```text
src/autodrift/decisive_history_env_runtime_smoke.py
tests/test_decisive_history_env_runtime_smoke.py
```

Updated:

```text
src/autodrift/decisive_history_env_hooks.py
```

The runtime smoke calls:

```text
AutoDriftEnv(spec.env_config)
env.reset(seed=spec.seed)
```

It intentionally does not call `env.step`, does not load a policy, and does not
materialize `DecisiveHistoryTaskCandidate` rows.

## Focused Tests

Command:

```bash
PYTHONPATH=src python -m pytest \
  tests/test_decisive_history_env_runtime_smoke.py \
  tests/test_decisive_history_env_hooks.py -q
```

Result:

```text
9 passed in 0.13s
```

The broader related focused set:

```bash
PYTHONPATH=src python -m pytest \
  tests/test_decisive_history_env_runtime_smoke.py \
  tests/test_decisive_history_env_hooks.py \
  tests/test_decisive_history_candidate_planner.py -q
```

Result:

```text
14 passed in 0.17s
```

## Runtime Smoke

Command:

```bash
PYTHONPATH=src python -m autodrift.decisive_history_env_runtime_smoke \
  --run-dir runs/m1506_decisive_history_env_hook_runtime_smoke \
  --seed-count 1
```

Output:

```text
summary=runs/m1506_decisive_history_env_hook_runtime_smoke/summary.json
reset_success_count=6
reset_failure_count=0
```

Summary:

```text
result_class: decisive_history_env_hook_runtime_smoke
runtime_scope: reset_only
hook_spec_count: 6
source_family_count: 6
reset_success_count: 6
reset_failure_count: 0
all_source_families_reset: true
guardrail_violation_count: 0
env_reset_called: true
env_step_called: false
```

Source-family results:

| Source family | Reset | Label | Friction step | Warmup gate |
| --- | ---: | --- | ---: | ---: |
| t4_actuator_delay_response | 1/1 | aeb_feasible | 0 | 1 |
| t4_capability_step_temporal | 1/1 | aeb_feasible | 1 | 0 |
| t4_staged_warmup_capability | 1/1 | aeb_feasible | 0 | 1 |
| t5_boundary_axis_retarget | 1/1 | aeb_feasible | 0 | 0 |
| t5_high_speed_close_obstacle | 1/1 | drift_required | 1 | 0 |
| t5_near_boundary_warmup | 1/1 | aeb_feasible | 0 | 1 |

## Guardrails

```text
actor_input_contract_changed: false
labels_enter_actor_input: false
candidate_materialized: false
policy_replay_started: false
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
level3_self_id_claim_made: false
```

## Interpretation

M1506 proves only that a tiny source-diverse subset of hook specs can instantiate
current-sim env configs and reset successfully. It does not prove that the
simulator can generate decisive-history candidates, because it does not run
policy rollout, terminal-margin measurement, current/recent/older-history
matching, or interventions.

The next milestone should design rollout candidate generation: how to collect
source histories, measure matching distances, run bounded intervention
variants, and convert only measured rollout evidence into
`DecisiveHistoryTaskCandidate` rows.

## Artifacts

```text
runs/m1506_decisive_history_env_hook_runtime_smoke/runtime_rows.csv
runs/m1506_decisive_history_env_hook_runtime_smoke/runtime_source_family_summary.csv
runs/m1506_decisive_history_env_hook_runtime_smoke/runtime_guardrail_summary.csv
runs/m1506_decisive_history_env_hook_runtime_smoke/summary.json
```

## Next Route

Route to:

```text
m1507-paper-route-decisive-history-rollout-candidate-design
```
