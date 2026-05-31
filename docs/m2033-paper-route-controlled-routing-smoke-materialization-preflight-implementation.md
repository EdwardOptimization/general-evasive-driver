# M2033 Paper-Route Controlled Routing Smoke Materialization Preflight Implementation

- status: completed
- decision: `controlled_routing_smoke_materialization_preflight_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2033-paper-route-controlled-routing-smoke-materialization-preflight-implementation.json`
- implementation: `src/autodrift/paper_route_controlled_routing_smoke_materialization_preflight.py`
- focused tests: `2 passed`
- compileall: `passed`
- summary: `runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/summary.json`
- selected sources: `runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/selected_smoke_sources.csv`
- executable specs: `runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json`
- planned workload: `runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/planned_workload.csv`
- reset/rollout/measured execution in M2033: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2033 implements the no-reset materialization adapter designed in M2032. It
converts the M2029 projected-ready source panel into a bounded routing-smoke
workload while preserving source provenance, controller profile metadata, and
claim boundaries.

This milestone is only a materialization preflight. It does not reset the
environment, execute policy actions, train, replay, rank controller families,
or validate paper-level T2/T3 task semantics.

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_controlled_routing_smoke_materialization_preflight \
  --panel-sources runs/m2029_paper_route_t2_t3_source_generation_preflight/merged_panel_sources.csv \
  --generated-source-specs runs/m2029_paper_route_t2_t3_source_generation_preflight/generated_source_specs.csv \
  --profile-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --output-dir runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight \
  --next-blocker m2034-paper-route-controlled-routing-smoke-materialization-preflight-result-audit
```

## Result

```text
result_class=controlled_routing_smoke_materialization_preflight_pass
input_source_count=237
selected_source_count=36
target_selected_source_count=36
executable_task_spec_count=36
planned_workload_count=432
target_workload_count=432
profile_count=12
target_profile_count=12
profile_missing_count=0
materialization_failure_count=0
duplicate_task_source_id_count=0
duplicate_workload_id_count=0
contract_violation_count=0
forbidden_key_violation_count=0
generated_non_proxy_count=0
smoke_proxy_paper_claim_count=0
guardrail_violation_count=0
```

Family coverage in the selected smoke subset:

```text
T1_reactive_active_safety: 4 source kinds
T2_same_current_different_older_history: 10 source kinds
T3_active_diagnostic_warmup: 10 source kinds
T4_variable_diagnostic_delay: 4 source kinds
T5_source_rich_extreme_dynamics: 8 source kinds
```

The selected sources crossed with the 12 registered controller profiles produce
`432` planned workload rows.

## Contract Boundary

Every materialized env config satisfies the deployable/human-view preflight
checks:

```text
history_length >= 1
action_history_mode == full
include_privileged_params == false
wheel_observation_mode == none
obstacle_relative_velocity_mode == zero
```

Generated T2/T3 source rows remain smoke proxies:

```text
materialization_semantics = smoke_proxy
paper_validity_claim = false
```

M2033 therefore supports only this claim:

```text
the controlled routing-smoke workload can be materialized with clean provenance,
profile artifacts, proxy labels, and guardrails.
```

It does not support:

```text
reset validity;
rollout validity;
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level generated-task validity;
level3 self-identification.
```

## Follow-up

M2034 must audit the M2033 artifacts before any reset-only validation command
or routing-smoke execution design. If the audit passes, the next admissible
route is a reset-only validation command design over the 36 executable specs;
direct rollout/ranking remains blocked.
