# M2048 Paper-Route Controlled Routing Smoke Task-Quality Repair Materialization Preflight Implementation

- status: completed
- decision: `controlled_routing_smoke_task_quality_repair_materialization_preflight_pass_route_to_result_audit`
- result class: `controlled_routing_smoke_task_quality_repair_materialization_preflight_pass`
- implementation: `src/autodrift/paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight.py`
- focused tests: `2 passed`
- summary: `runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/summary.json`
- reset/rollout/measured execution in M2048: `false`
- policy actions executed in M2048: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight.py
```

Result:

```text
2 passed
```

No-reset materialization preflight:

```bash
PYTHONPATH=src python -m autodrift.paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight \
  --templates configs/paper_route_controlled_routing_smoke_task_quality_repair_candidates_v0.json \
  --parent-specs runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json \
  --parent-workload runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/planned_workload.csv \
  --source-profile-localization runs/m2042_paper_route_controlled_routing_smoke_outcome_localization/outcome_by_source_profile.csv \
  --output-dir runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight \
  --next-blocker m2049-paper-route-controlled-routing-smoke-task-quality-repair-materialization-preflight-result-audit
```

Result:

```text
result_class=controlled_routing_smoke_task_quality_repair_materialization_preflight_pass
repaired_spec_count=192
planned_workload_count=2304
unresolved_parent_count=0
guardrail_violation_count=0
```

## Pass Gates

The preflight passes the registered gates:

```text
input_candidate_count: 192
expected_candidate_count: 192
repaired_spec_count: 192
planned_workload_count: 2304
expected_workload_count: 2304
profile_count: 12
target_profile_count: 12
unresolved_parent_count: 0
materialization_failure_count: 0
duplicate_task_source_id_count: 0
duplicate_workload_id_count: 0
contract_violation_count: 0
forbidden_key_violation_count: 0
generated_proxy_paper_claim_count: 0
profile_specific_tuning_count: 0
forbidden_claim_count: 0
guardrail_violation_count: 0
```

Repair-axis quotas:

```text
l2_offtrack_relief: 64
family_offtrack_relief: 48
zero_success_source_kind_relief: 40
success_neighborhood_expansion: 24
generated_proxy_support_check: 16
```

Split quotas:

```text
public_debug: 112
public_gate: 80
```

## What Changed

M2048 adds deterministic parent resolution and materialization:

```text
exact_task_source_id;
source_profile_offtrack_slice;
family_slice;
source_kind_slice;
generated_proxy_slice.
```

It clones resolved M2033 parent specs, applies task-quality deltas from M2045
templates, preserves human-view actor contract fields, and writes repaired
spec/workload artifacts. It does not run reset or rollout.

## Supported Claims

Supported:

```text
The M2045 templates can be materialized into repaired executable task specs.
The repaired panel has 192 specs and 2304 workload rows.
Parent resolution, contract guards, claim guards, and quota guards pass.
The repaired panel is ready for result audit before reset validation design.
```

Unsupported:

```text
reset validity;
rollout validity;
measured execution success;
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark result;
level3 self-identification.
```

## Next

M2049 should audit the materialization result before reset validation command
design. Direct reset, measured execution, ranking, paper comparison, and
self-ID claims remain blocked until admitted by the audit.
