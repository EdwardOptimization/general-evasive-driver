# M2039 Paper-Route Controlled Routing Smoke Measured Execution Implementation and Run

- status: completed
- decision: `controlled_routing_smoke_measured_execution_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2039-paper-route-controlled-routing-smoke-measured-execution-implementation-and-run.json`
- implementation: `src/autodrift/paper_route_controlled_routing_smoke_measured_runner.py`
- focused tests: `3 passed`
- summary: `runs/m2039_paper_route_controlled_routing_smoke_measured_execution/summary.json`
- measured execution in M2039: `true`
- rollout/policy actions in M2039: `true`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2039 implements the focused measured runner designed in M2038 and runs the
exact 432-row controlled routing-smoke workload. The runner preserves M2033
panel/proxy metadata and writes complete measured rollout artifacts without
ranking controller families.

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_controlled_routing_smoke_measured_runner \
  --executable-task-specs runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json \
  --workload runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/planned_workload.csv \
  --output-dir runs/m2039_paper_route_controlled_routing_smoke_measured_execution \
  --eval-seed-base 203900 \
  --device cpu \
  --target-episode-count 432 \
  --target-spec-count 36 \
  --target-profile-count 12 \
  --next-blocker m2040-paper-route-controlled-routing-smoke-measured-execution-result-audit
```

## Completeness Result

```text
result_class=controlled_routing_smoke_measured_execution_pass
episode_count=432
target_episode_count=432
failure_count=0
spec_count=36
target_spec_count=36
profile_count=12
target_profile_count=12
metadata_missing_count=0
metric_completeness_failure_count=0
all_selected_metrics_finite=true
family_quota_pass=true
source_kind_quota_pass=true
proxy_template_quota_pass=true
generated_proxy_quota_pass=true
guardrail_violation_count=0
environment_rollout_started=true
policy_action_executed=true
measured_rollout_started=true
controller_family_ranking_claim_made=false
paper_level_claim_made=false
finite_window_vs_gru_conclusion_made=false
level3_self_id_claim_made=false
```

## Raw Outcome Snapshot

The run completed, but raw outcomes are low-support and offtrack-heavy:

```text
success_obstacle_pass: 20
collision_failure: 13
off_track_noncollision_noncompletion: 399
success_rate: 0.046296
collision_rate: 0.030093
clearance_margin_mean: 10.530665
```

This is not a ranking conclusion. M2040 must audit whether these outcomes are
usable for a bounded comparison, require outcome localization, or require task
quality repair.

## Artifacts

```text
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/summary.json
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/episode_rows.csv
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/failure_rows.csv
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/validation_failure_rows.csv
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/metric_completeness_failures.csv
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/metadata_missing_rows.csv
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/profile_aggregate.csv
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/family_aggregate.csv
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/source_kind_aggregate.csv
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/proxy_template_aggregate.csv
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/generated_proxy_aggregate.csv
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/outcome_aggregate.csv
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/termination_reason_aggregate.csv
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/claim_boundary.csv
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/run_state.json
```

## Claim Boundary

M2039 supports only:

```text
the controlled routing-smoke workload was executed completely and produced
measured rollout artifacts with clean metadata and guardrails.
```

It does not support:

```text
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
paper-valid generated T2/T3 task semantics;
level3 self-identification.
```

## Follow-up

M2040 must audit the result before any ranking or repair. The likely audit
questions are:

```text
Is the 432-row execution complete and clean? yes.
Is it comparison-ready as-is? likely no, because outcomes are offtrack-heavy.
Should the next route be outcome localization rather than ranking? likely yes.
```
