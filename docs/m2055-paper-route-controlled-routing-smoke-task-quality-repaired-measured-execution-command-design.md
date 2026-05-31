# M2055 Paper-Route Controlled Routing Smoke Task-Quality Repaired Measured Execution Command Design

- status: completed
- decision: `controlled_routing_smoke_task_quality_repaired_measured_command_design_route_to_existing_runner_execution`
- manifest: `experiments/manifests/m2055-paper-route-controlled-routing-smoke-task-quality-repaired-measured-execution-command-design.json`
- parent synthesis: `docs/m2054-paper-route-controlled-routing-smoke-task-quality-repair-reset-validator-normalization-result-audit.md`
- executable specs: `runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/executable_task_specs.json`
- planned workload: `runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/planned_workload.csv`
- measured execution in M2055: `false`
- rollout/policy actions in M2055: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2055 designs the measured-execution route for the repaired reset-valid
controlled-routing-smoke workload. It does not run rollout or policy actions.

Target execution scope:

```text
executable task specs: 192
controller profiles: 12
planned workload rows: 2304
eval_seed_base: 205600
device: cpu
```

## Runner Compatibility Audit

Use the existing focused runner:

```text
autodrift.paper_route_controlled_routing_smoke_measured_runner
```

The runner is compatible with the repaired M2048 artifacts because it consumes:

```text
--executable-task-specs
--workload
--target-episode-count
--target-spec-count
--target-profile-count
```

and validates the required controlled-routing-smoke schema:

```text
workload_id
task_source_id
profile_name
profile_config_path
checkpoint_path
panel_task_family
source_kind
proxy_template_family
generated_source_row
paper_validity_claim
```

M2048 planned workload rows contain these fields. The repaired specs also keep
the controlled-routing-smoke metadata used by the runner and reset validator.
Additional repair metadata such as `repair_axis`, `source_split`,
`repair_candidate_id`, and `parent_resolution_method` remains available in the
M2048 artifacts, but it is not required for measured execution completeness and
must not enter actor input.

The runner already canonicalizes generated-proxy `paper_validity_claim` keys in
its aggregate comparison, matching the M2053 reset-validator normalization.

## M2056 Command

M2056 should run exactly:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_controlled_routing_smoke_measured_runner.py
```

Then:

```bash
PYTHONPATH=src python -m autodrift.paper_route_controlled_routing_smoke_measured_runner \
  --executable-task-specs runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/executable_task_specs.json \
  --workload runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/planned_workload.csv \
  --output-dir runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution \
  --eval-seed-base 205600 \
  --device cpu \
  --target-episode-count 2304 \
  --target-spec-count 192 \
  --target-profile-count 12 \
  --next-blocker m2057-paper-route-controlled-routing-smoke-task-quality-repaired-measured-execution-result-audit
```

## Required Artifacts

M2056 must write:

```text
runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/summary.json
runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/episode_rows.csv
runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/failure_rows.csv
runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/validation_failure_rows.csv
runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/metric_completeness_failures.csv
runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/metadata_missing_rows.csv
runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/profile_aggregate.csv
runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/family_aggregate.csv
runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/source_kind_aggregate.csv
runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/proxy_template_aggregate.csv
runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/generated_proxy_aggregate.csv
runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/outcome_aggregate.csv
runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/termination_reason_aggregate.csv
runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/claim_boundary.csv
runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/run_state.json
```

## Pass Gates

M2056 passes only if:

```text
result_class == controlled_routing_smoke_measured_execution_pass
episode_count == 2304
target_episode_count == 2304
failure_count == 0
spec_count == 192
target_spec_count == 192
profile_count == 12
target_profile_count == 12
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

If validation fails before rollout, M2056 must fail closed with
`episode_count=0` and write `validation_failure_rows.csv`. If rollout failures
occur, they must be preserved in `failure_rows.csv` and interpreted only in
M2057.

## Claim Boundary

M2056 measured execution, even if complete, may claim only:

```text
the repaired controlled-routing-smoke workload was executed and produced
complete measured rollout artifacts.
```

It cannot claim:

```text
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
paper-valid generated task semantics;
level3 self-identification.
```

## Next

Next milestone:

```text
m2056-paper-route-controlled-routing-smoke-task-quality-repaired-measured-execution-implementation-and-run
```

M2056 may run only the frozen measured-execution command. Interpretation must
be deferred to M2057 result audit.
