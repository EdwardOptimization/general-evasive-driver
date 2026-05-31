# M2035 Paper-Route Controlled Routing Smoke Reset Validation Command Design

- status: completed
- decision: `controlled_routing_smoke_reset_command_design_route_to_focused_validator_implementation_and_run`
- manifest: `experiments/manifests/m2035-paper-route-controlled-routing-smoke-reset-validation-command-design.json`
- parent audit: `docs/m2034-paper-route-controlled-routing-smoke-materialization-preflight-result-audit.md`
- executable specs: `runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json`
- reset execution in M2035: `false`
- rollout/measured execution in M2035: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2035 freezes the reset-validation route for the M2033 controlled routing-smoke
36-spec executable panel. It does not run reset. The next milestone may
implement and run reset-only validation if it preserves the exact schema and
guardrails below.

Target:

```text
input executable task specs: 36
reset attempts: 36
expected observation dimension: 72
rollout steps: 0
policy actions: 0
```

## Validator Decision

Do not reuse the older reset validators directly.

The generic task-quality validator can reset `env_config` entries, but its
artifact schema is tied to fields such as:

```text
candidate_source_id
feasibility_tier_id
surface_variant
```

The calibrated validator preserves a different repair schema:

```text
repair_source_kind
selection_quota_name
base_geometry_source
representative_cell_rule
```

The M2033 executable specs instead require controlled-routing-smoke metadata:

```text
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

Therefore M2036 should implement a focused reset validator:

```text
autodrift.paper_route_controlled_routing_smoke_reset_validation_preflight
```

It may call the existing low-level reset helper logic, but its output rows,
aggregates, summary, and claim boundary must preserve M2033 metadata instead of
forcing older task-quality columns.

## M2036 Command

M2036 should run exactly:

```bash
PYTHONPATH=src python -m autodrift.paper_route_controlled_routing_smoke_reset_validation_preflight \
  --executable-task-specs runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json \
  --output-dir runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight \
  --eval-seed-base 203600 \
  --target-spec-count 36 \
  --expected-observation-dim 72 \
  --next-blocker m2037-paper-route-controlled-routing-smoke-reset-validation-result-audit
```

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_controlled_routing_smoke_reset_validation_preflight.py
```

## Expected Artifacts

M2036 must write:

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

Each reset row must preserve:

```text
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
eval_seed
reset_success
observation_length
observation_finite
obstacle_initialized
environment_reset_started
environment_rollout_started
policy_action_executed
```

## M2036 Pass Gates

M2036 passes only if:

```text
result_class == controlled_routing_smoke_reset_validation_preflight_pass
input_executable_spec_count == 36
target_executable_spec_count == 36
reset_attempt_count == 36
reset_success_count == 36
reset_failure_count == 0
observation_finite_count == 36
observation_dimension_failure_count == 0
obstacle_initialized_count == 36
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

If any reset fails, M2036 must fail closed and route to result/failure audit. It
must not repair and rerun inside the same milestone.

## Claim Boundary

If M2036 passes, it may claim only:

```text
the M2033 controlled routing-smoke 36-spec public diagnostic panel is reset-valid
under the current simulator and strict human-view observation contract.
```

It still cannot claim:

```text
rollout success;
measured execution success;
controller-family ranking;
finite-window-vs-GRU comparison;
paper-level benchmark evidence;
paper-valid generated T2/T3 task semantics;
level3 self-identification.
```

## Next

Next milestone:

```text
m2036-paper-route-controlled-routing-smoke-reset-validation-implementation-and-run
```

M2036 may implement the focused validator and run only the frozen reset-only
command. Interpretation must be deferred to M2037 result audit.
