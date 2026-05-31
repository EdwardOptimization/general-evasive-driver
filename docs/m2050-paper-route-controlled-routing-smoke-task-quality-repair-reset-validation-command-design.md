# M2050 Paper-Route Controlled Routing Smoke Task-Quality Repair Reset Validation Command Design

- status: completed
- decision: `controlled_routing_smoke_task_quality_repair_reset_command_design_route_to_existing_validator_run`
- manifest: `experiments/manifests/m2050-paper-route-controlled-routing-smoke-task-quality-repair-reset-validation-command-design.json`
- parent audit: `docs/m2049-paper-route-controlled-routing-smoke-task-quality-repair-materialization-preflight-result-audit.md`
- executable specs: `runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/executable_task_specs.json`
- reset execution in M2050: `false`
- rollout/measured execution in M2050: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2050 freezes the reset-validation route for the M2048 repaired
controlled-routing-smoke `192`-spec executable panel. It does not run reset.
The next milestone may run reset-only validation if it uses the exact command
and gates below.

Target:

```text
input executable task specs: 192
reset attempts: 192
expected observation dimension: 72
rollout steps: 0
policy actions: 0
```

## Validator Decision

Reuse the existing focused validator:

```text
autodrift.paper_route_controlled_routing_smoke_reset_validation_preflight
```

Reason:

```text
M2048 repaired specs preserve the controlled-routing-smoke metadata schema used
by the validator:

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
source_reference
materialization_semantics
proxy_template_family
generated_source_row
paper_validity_claim
```

M2048 also adds repair-specific metadata such as `repair_axis`, `source_split`,
and `parent_resolution_method`. Those fields are not required for reset
validity; they remain available in the materialized spec/workload artifacts and
are not used as actor inputs. M2051 therefore does not need a new validator
implementation unless the existing reset run exposes a schema failure.

## M2051 Command

M2051 should run exactly:

```bash
PYTHONPATH=src python -m autodrift.paper_route_controlled_routing_smoke_reset_validation_preflight \
  --executable-task-specs runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/executable_task_specs.json \
  --output-dir runs/m2051_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight \
  --eval-seed-base 205100 \
  --target-spec-count 192 \
  --expected-observation-dim 72 \
  --next-blocker m2052-paper-route-controlled-routing-smoke-task-quality-repair-reset-validation-result-audit
```

Focused validator tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_controlled_routing_smoke_reset_validation_preflight.py
```

## Expected Artifacts

M2051 must write:

```text
runs/m2051_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight/summary.json
runs/m2051_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight/reset_rows.csv
runs/m2051_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight/reset_failure_rows.csv
runs/m2051_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight/contract_rows.csv
runs/m2051_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight/reset_distribution_by_family.csv
runs/m2051_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight/reset_distribution_by_source_kind.csv
runs/m2051_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight/reset_distribution_by_proxy_template.csv
runs/m2051_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight/reset_distribution_by_generated_proxy.csv
runs/m2051_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight/metadata_missing_rows.csv
runs/m2051_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight/claim_boundary.csv
```

Each reset row must preserve the controlled-routing-smoke metadata fields listed
above and include:

```text
eval_seed
reset_success
observation_length
expected_observation_length
observation_dimension_matches
observation_finite
obstacle_initialized
contract_violation_count
environment_reset_started
environment_rollout_started
policy_action_executed
```

## M2051 Pass Gates

M2051 passes only if:

```text
result_class == controlled_routing_smoke_reset_validation_preflight_pass
input_executable_spec_count == 192
target_executable_spec_count == 192
reset_attempt_count == 192
reset_success_count == 192
reset_failure_count == 0
observation_finite_count == 192
observation_dimension_failure_count == 0
obstacle_initialized_count == 192
contract_violation_count == 0
metadata_missing_count == 0
forbidden_key_violation_count == 0
family_quota_pass == true
source_kind_quota_pass == true
proxy_template_quota_pass == true
generated_proxy_quota_pass == true
guardrail_violation_count == 0
environment_reset_started == true
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
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

If any reset fails, M2051 must fail closed and route to result/failure audit. It
must not repair and rerun inside the same milestone.

## Claim Boundary

If M2051 passes, it may claim only:

```text
the M2048 repaired controlled-routing-smoke 192-spec diagnostic panel is
reset-valid under the current simulator and strict human-view observation
contract.
```

It still cannot claim:

```text
rollout success;
measured execution success;
controller-family ranking;
finite-window-vs-GRU comparison;
paper-level benchmark evidence;
paper-valid generated task semantics;
level3 self-identification.
```

## Next

Next milestone:

```text
m2051-paper-route-controlled-routing-smoke-task-quality-repair-reset-validation-implementation-and-run
```

M2051 may run only the frozen reset-only command. Interpretation must be
deferred to M2052 result audit.
