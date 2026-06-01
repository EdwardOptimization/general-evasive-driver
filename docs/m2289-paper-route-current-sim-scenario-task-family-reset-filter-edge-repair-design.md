# M2289 Paper-Route Current-Sim Scenario Task-Family Reset Filter-Edge Repair Design

- status: completed
- decision: `current_sim_scenario_task_family_filter_edge_repair_design_admit_implementation`
- manifest: `experiments/manifests/m2289-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-design.json`
- parent audit: `docs/m2288-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-result-audit.md`
- reset execution in M2289: `false`
- rollout/measured execution in M2289: `false`
- policy actions executed in M2289: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2289 freezes a focused repair for the single M2287 reset failure:

```text
M2287 reset successes: 71 / 72
remaining failed row: m2277_r4_02
failure class: scenario_sampling_failure / friction_step_timing_filter_not_in_materializer_precheck
```

The repair must preserve:

```text
P0 actor contract
metadata-only role labels
72-spec role-family structure
left/right lateral sign convention
no rollout/training/ranking claims
```

## Design Decision

For the v0 reset-valid role-family pack, do not silently mix the `low_mu`
hidden-dynamics bucket with a friction-step event.

Rationale:

```text
low_mu already appears as the exact initial mu range chosen by the materializer;
friction_step is a separate temporal disturbance;
M2273-M2289 scenario/task-quality work is still establishing a reset-valid
role-family pack, not yet a sudden-friction-change task family.
```

Therefore M2290 should remove the unconditional materializer rule:

```text
if hidden_bucket == "low_mu":
    friction_step.enabled = true
```

The reset-valid v0 pack should leave:

```text
friction_step.enabled: false
```

for every materialized role row.

Sudden friction loss, split-mu, tire blowout, wheel fault, or actuator fault
families remain future scenario-family extensions and should not be silently
approximated inside this reset-valid v0 pack.

## Filter-Aware Precheck

M2290 should also add a small materializer-side reset-filter compatibility
helper. The helper should make the deterministic materialization precheck cover
the sampler filters that can reject a candidate before any environment reset:

```text
label in obstacle.allowed_labels
require_aeb_infeasible
friction_limited_speed cap
friction_step timing compatibility if friction_step.enabled
```

For the repaired v0 pack, the friction-step branch should be trivially
compatible because `friction_step.enabled == false`. The helper is still useful
because it prevents future materializer changes from reintroducing a
classifier-only precheck gap.

## Implementation Scope

M2290 may edit:

```text
src/autodrift/paper_route_current_sim_scenario_task_family_config_materialization.py
tests/test_paper_route_current_sim_scenario_task_family_config_materialization.py
configs/paper_route_current_sim_scenario_task_family_v0.json
```

M2290 should not edit:

```text
src/autodrift/env.py
src/autodrift/paper_route_current_sim_scenario_task_family_reset_validation.py
P0 actor observation fields
role labels or actor contract semantics
```

## Required Tests

Focused tests should assert:

```text
all materialized specs have friction_step.enabled == false
deterministic center classifier labels remain allowed
deterministic center targets are reset-filter compatible
left_offset remains positive and right_offset remains negative
P0 actor contract stays clean
```

## M2290 Commands

Run focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_scenario_task_family_config_materialization.py \
  tests/test_paper_route_current_sim_scenario_task_family_reset_validation.py \
  tests/test_obstacle_lateral_offset_instrumentation.py
```

Rerun materialization:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_config_materialization \
  --config-output configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2290_paper_route_current_sim_scenario_task_family_filter_edge_repair/materialization \
  --next-blocker m2290-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-implementation
```

Run reset-only validation:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_reset_validation \
  --config configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2290_paper_route_current_sim_scenario_task_family_filter_edge_repair/reset_validation \
  --eval-seed-base 229000 \
  --target-spec-count 72 \
  --expected-observation-dim 72 \
  --next-blocker m2291-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-result-audit
```

## Pass Gates

M2290 passes only if:

```text
focused tests pass
materialization result_class == current_sim_scenario_task_family_config_materialization_pass
scenario_spec_count == 72
unsupported_execution_blocker_count == 0
actor_contract_violation_count == 0
labels_enter_actor_input_count == 0
ranking_admissible_count == 0
guardrail_violation_count == 0

reset result_class == current_sim_scenario_task_family_reset_validation_pass
reset_attempt_count == 72
reset_success_count == 72
reset_failure_count == 0
observation_dimension_failure_count == 0
actor_contract_violation_count == 0
label_not_allowed_count == 0
single_label_exact_mismatch_count == 0
lateral_offset_numeric_mismatch_count == 0
lateral_bucket_mismatch_count == 0
reset guardrail_violation_count == 0
```

If M2290 fails, it must still write artifacts and route to result audit. It must
not repair and rerun again inside M2290.

## Claim Boundary

If M2290 passes, it may claim only:

```text
the current-sim role-family scenario pack is materialized and reset-valid under
the P0 actor contract.
```

It still cannot claim:

- rollout success;
- measured execution success;
- training result;
- controller-family ranking;
- winner selection;
- finite-window vs GRU conclusion;
- paper-level result;
- level3 self-identification.

## Next

Pre-register:

```text
m2290-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-implementation
```
