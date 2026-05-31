# M2038 Paper-Route Controlled Routing Smoke Measured Execution Command Design

- status: completed
- decision: `controlled_routing_smoke_measured_command_design_route_to_focused_runner_implementation_and_run`
- manifest: `experiments/manifests/m2038-paper-route-controlled-routing-smoke-measured-execution-command-design.json`
- parent audit: `docs/m2037-paper-route-controlled-routing-smoke-reset-validation-result-audit.md`
- executable specs: `runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json`
- planned workload: `runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/planned_workload.csv`
- measured execution in M2038: `false`
- rollout/policy actions in M2038: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2038 designs the measured execution route for the reset-valid M2033 controlled
routing-smoke workload. It does not run rollout or policy actions.

Target execution scope:

```text
executable task specs: 36
controller profiles: 12
planned workload rows: 432
eval_seed_base: 203900
device: cpu
```

## Runner Compatibility Audit

### `controller_family_measured_routing_smoke.py`

Rejected for this branch.

It is useful historical routing-smoke code, but it is hard-coded around the old
M1674/M1686 route:

```text
4 selected hook specs x 12 profiles = 48 episodes
task_source_id = m1686-spec-...
source_family from default_hook_specs
```

It does not consume the M2033 `executable_task_specs.json` or
`planned_workload.csv`, and therefore cannot preserve the 36 source-kind
representatives or the M2029/M2033 provenance fields.

### `executable_v2_task_quality_calibrated_measured_runner.py`

Rejected for direct reuse.

It has useful rollout mechanics, resume handling, failure rows, metric
completeness checks, and profile caching. But its validation and metadata schema
are calibrated task-quality specific:

```text
repair_source_kind
repair_candidate_id
selection_quota_name
base_geometry_source
representative_cell_rule
```

The M2033 workload has controlled-routing-smoke fields instead:

```text
panel_task_family
source_kind
source_edge
source_origin
materialization_semantics
proxy_template_family
generated_source_row
paper_validity_claim
```

Forcing M2033 through the calibrated runner would either fail closed on missing
repair fields or produce lossy artifacts. That would make the later comparison
hard to audit.

## Decision

M2039 should implement a focused measured runner:

```text
autodrift.paper_route_controlled_routing_smoke_measured_runner
```

It should reuse safe low-level rollout utilities where possible, but it must own
the M2033 metadata schema and output contract.

## M2039 Command

M2039 should run exactly:

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

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_controlled_routing_smoke_measured_runner.py
```

## Required Artifacts

M2039 must write:

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

Episode and failure rows must preserve:

```text
workload_id
task_source_id
panel_source_id
panel_task_family
source_origin
source_kind
source_edge
window_tag
source_role_semantics
parent_feasibility_tier_id
normalized_surface_variant
sampled_obstacle_label
materialization_semantics
proxy_template_family
generated_source_row
paper_validity_claim
profile_name
profile_config_path
checkpoint_path
eval_seed
```

## Pass Gates

M2039 passes only if:

```text
result_class == controlled_routing_smoke_measured_execution_pass
episode_count == 432
target_episode_count == 432
failure_count == 0
spec_count == 36
profile_count == 12
metadata_missing_count == 0
family_quota_pass == true
source_kind_quota_pass == true
proxy_template_quota_pass == true
generated_proxy_quota_pass == true
metric_completeness_failure_count == 0
guardrail_violation_count == 0
environment_rollout_started == true
policy_action_executed == true
measured_rollout_started == true
training_started == false
replay_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
profile_specific_tuning == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
```

If validation fails before rollout, M2039 must fail closed with `episode_count=0`
and write `validation_failure_rows.csv`. If rollout failures occur, they must be
preserved in `failure_rows.csv` and interpreted only in M2040.

## Claim Boundary

M2039 measured execution, even if complete, may claim only:

```text
the controlled routing-smoke workload was executed and produced complete
measured rollout artifacts.
```

It cannot claim:

```text
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
paper-valid generated T2/T3 task semantics;
level3 self-identification.
```

Ranking or interpretation requires a separate result audit and comparison
discipline after execution.

## Next

Next milestone:

```text
m2039-paper-route-controlled-routing-smoke-measured-execution-implementation-and-run
```

M2039 may implement the focused runner and execute only the frozen 432-row
measured workload. Interpretation must be deferred to M2040 result audit.
