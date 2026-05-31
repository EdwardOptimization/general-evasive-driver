# M2036 Paper-Route Controlled Routing Smoke Reset Validation Implementation and Run

- status: completed
- decision: `controlled_routing_smoke_reset_validation_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2036-paper-route-controlled-routing-smoke-reset-validation-implementation-and-run.json`
- implementation: `src/autodrift/paper_route_controlled_routing_smoke_reset_validation_preflight.py`
- focused tests: `1 passed`
- summary: `runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight/summary.json`
- reset execution in M2036: `true`
- rollout/measured execution in M2036: `false`
- policy actions executed: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2036 implements the focused reset-only validator designed in M2035 and runs the
exact 36-spec controlled routing-smoke reset validation. The validator preserves
M2033 metadata in reset rows and aggregates instead of forcing the older
task-quality or calibrated repair schemas.

This milestone tests only reset validity and observation-contract validity. It
does not execute rollout steps or policy actions.

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_controlled_routing_smoke_reset_validation_preflight \
  --executable-task-specs runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json \
  --output-dir runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight \
  --eval-seed-base 203600 \
  --target-spec-count 36 \
  --expected-observation-dim 72 \
  --next-blocker m2037-paper-route-controlled-routing-smoke-reset-validation-result-audit
```

## Result

```text
result_class=controlled_routing_smoke_reset_validation_preflight_pass
input_executable_spec_count=36
target_executable_spec_count=36
reset_attempt_count=36
reset_success_count=36
reset_failure_count=0
observation_finite_count=36
observation_dimension_failure_count=0
obstacle_initialized_count=36
contract_violation_count=0
metadata_missing_count=0
forbidden_key_violation_count=0
family_quota_pass=true
source_kind_quota_pass=true
proxy_template_quota_pass=true
generated_proxy_quota_pass=true
guardrail_violation_count=0
environment_reset_started=true
environment_rollout_started=false
policy_action_executed=false
```

Artifacts:

```text
runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight/summary.json
runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight/reset_rows.csv
runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight/reset_failure_rows.csv
runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight/contract_rows.csv
runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight/reset_distribution_by_family.csv
runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight/reset_distribution_by_source_kind.csv
runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight/reset_distribution_by_proxy_template.csv
runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight/reset_distribution_by_generated_proxy.csv
runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight/metadata_missing_rows.csv
runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight/claim_boundary.csv
```

## Interpretation

M2036 proves that the M2033 36-spec controlled routing-smoke panel is reset-valid
under the current simulator and human-view observation contract.

It does not prove:

```text
rollout success;
controller-family performance;
controller-family ranking;
finite-window-vs-GRU comparison;
paper-valid generated T2/T3 task semantics;
paper-level benchmark evidence;
level3 self-identification.
```

The generated T2/T3 rows remain smoke proxies and must not be promoted into
paper-valid task semantics without later task-semantics validation.

## Follow-up

M2037 must audit this reset pass before any measured/routing-smoke execution
command design. If accepted, the next route can design measured execution over
the already materialized 432-row planned workload; direct ranking remains
blocked until measured execution and result audit exist.
