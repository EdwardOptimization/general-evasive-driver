# M1505 Paper-Route Decisive History Env-Hook Implementation

## Summary

M1505 implements the no-training env-hook/spec scaffolding designed in M1504.

Decision:

```text
decisive_history_env_hook_implemented_admit_runtime_smoke
```

This milestone does not run simulator rollout, replay, PPO, training,
promotion, private holdout, corpus export, actor-input changes, or level3
self-ID claims.

## Implementation

Added:

```text
src/autodrift/decisive_history_env_hooks.py
tests/test_decisive_history_env_hooks.py
```

The module provides:

```text
DecisiveHistoryEnvHookSpec
DecisiveHistoryHookArtifacts
source_plan_to_hook_specs
default_hook_specs
env_config_for_hook_spec
hook_spec_to_candidate_stub
hook_spec_to_row
build_env_hook_summary
run_env_hook_dry_smoke
```

It converts M1502 `CandidateSourcePlan` rows into P0-compatible
`DriftEnvConfig` objects for the six M1501 source families while keeping
candidate materialization and simulator runtime separate.

## Source-Family Coverage

The dry hook layer covers:

```text
t4_staged_warmup_capability
t4_capability_step_temporal
t4_actuator_delay_response
t5_near_boundary_warmup
t5_high_speed_close_obstacle
t5_boundary_axis_retarget
```

Family-specific hooks include:

```text
warmup_gate.enabled for staged/warmup/actuator-response families;
friction_step.enabled for temporal/high-speed capability-step families;
high-speed close-obstacle speed ranges with friction_limited_speed disabled;
obstacle_relative_velocity_mode = "zero";
wheel_observation_mode = "none";
include_privileged_params = false;
history_length = 1.
```

## Focused Tests

Command:

```bash
PYTHONPATH=src python -m pytest tests/test_decisive_history_env_hooks.py -q
```

Result:

```text
6 passed in 0.21s
```

Covered behavior:

```text
default hook specs cover all six T4/T5 source families;
env configs preserve the P0 no-wheel/no-privileged actor contract;
invalid source plans are rejected;
candidate stubs remain schema-only and non-materialized;
dry smoke writes required artifacts without rollout/replay/training/PPO;
guardrail violations are counted if labels would enter actor input.
```

## Dry Smoke

Command:

```bash
PYTHONPATH=src python -m autodrift.decisive_history_env_hooks \
  --run-dir runs/m1505_decisive_history_env_hook_dry_smoke \
  --seed-count 2
```

Output:

```text
summary=runs/m1505_decisive_history_env_hook_dry_smoke/summary.json
hook_spec_count=12
guardrail_violation_count=0
```

Summary:

```text
result_class: decisive_history_env_hook_dry_smoke
hook_spec_count: 12
source_family_count: 6
task_family_counts: T4=6, T5=6
unique_seeds: 12
unique_capability_pairs: 8
unique_geometry_keys: 12
unique_reveal_steps: 12
guardrail_violation_count: 0
```

Source-family rows:

```text
t4_actuator_delay_response: 2 specs, friction_step 0, warmup_gate 2
t4_capability_step_temporal: 2 specs, friction_step 2, warmup_gate 0
t4_staged_warmup_capability: 2 specs, friction_step 0, warmup_gate 2
t5_boundary_axis_retarget: 2 specs, friction_step 0, warmup_gate 0
t5_high_speed_close_obstacle: 2 specs, friction_step 2, warmup_gate 0
t5_near_boundary_warmup: 2 specs, friction_step 0, warmup_gate 2
```

## Guardrails

```text
labels_enter_actor_input: false
candidate_materialized: false
simulator_rollout_started: false
training_started: false
evaluation_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
level3_self_id_claim_made: false
```

## Interpretation

M1505 proves only that the source-plan-to-env-config hook layer is implemented,
test-covered, and dry-smoke artifact compatible. It does not prove that the
current simulator can reset or roll out every hook spec, and it does not
materialize `DecisiveHistoryTaskCandidate` evidence.

The next step should be a reset-only/current-sim runtime smoke over a tiny
source-diverse subset. That milestone may instantiate `AutoDriftEnv` and call
`reset`, but it should not run policy replay, PPO, training, promotion, private
holdout, or corpus export.

## Artifacts

```text
runs/m1505_decisive_history_env_hook_dry_smoke/hook_spec_rows.csv
runs/m1505_decisive_history_env_hook_dry_smoke/hook_source_family_summary.csv
runs/m1505_decisive_history_env_hook_dry_smoke/hook_guardrail_summary.csv
runs/m1505_decisive_history_env_hook_dry_smoke/summary.json
```

## Next Route

Route to:

```text
m1506-paper-route-decisive-history-env-hook-runtime-smoke
```
