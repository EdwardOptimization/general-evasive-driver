# M2065 Paper-Route Outcome-Supported Decisive Reset-Validation Command Design

- status: completed
- decision: `outcome_supported_decisive_reset_validation_command_design_route_to_focused_validator`
- parent audit: `docs/m2064-paper-route-outcome-supported-decisive-materialization-preflight-result-audit.md`
- executable specs: `runs/m2063_paper_route_outcome_supported_decisive_materialization_preflight/executable_task_specs.json`
- reset execution in M2065: `false`
- rollout/measured execution in M2065: `false`
- policy actions executed in M2065: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2065 freezes the reset-validation route for the M2063 materialized
outcome-supported decisive `240`-spec panel. It does not run reset.

Target:

```text
input executable task specs: 240
reset attempts: 240
expected observation dimension: 72
rollout steps: 0
policy actions: 0
```

## Validator Decision

Do not reuse `autodrift.paper_route_controlled_routing_smoke_reset_validation_preflight`
as-is.

Reason:

```text
that wrapper expects older controlled-routing-smoke metadata fields such as
panel_source_id, source_role_semantics, parent_feasibility_tier_id,
normalized_surface_variant, sampled_obstacle_label, and source_reference.

M2063 intentionally preserves the M2060 candidate schema instead:
candidate_id, candidate_set_id, branch_id, source_split, task_role_semantics,
difficulty axes, warmup fields, same-current metadata, and terminal bucket.
```

Reusing the old wrapper would create false metadata-missing failures. M2066
should implement a focused wrapper:

```text
autodrift.paper_route_outcome_supported_decisive_reset_validation_preflight
```

It may reuse the low-level reset helper:

```text
autodrift.executable_v2_task_quality_reset_validation_preflight.reset_task_quality_spec
```

but must preserve and audit the M2063 schema.

## M2066 Command

M2066 should run exactly:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_outcome_supported_decisive_reset_validation_preflight.py

PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_reset_validation_preflight \
  --executable-task-specs runs/m2063_paper_route_outcome_supported_decisive_materialization_preflight/executable_task_specs.json \
  --output-dir runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight \
  --eval-seed-base 206600 \
  --target-spec-count 240 \
  --expected-observation-dim 72 \
  --next-blocker m2067-paper-route-outcome-supported-decisive-reset-validation-result-audit
```

## Expected Artifacts

M2066 should write:

```text
runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight/summary.json
runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight/reset_rows.csv
runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight/reset_failure_rows.csv
runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight/contract_rows.csv
runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight/metadata_missing_rows.csv
runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight/reset_distribution_by_family.csv
runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight/reset_distribution_by_split.csv
runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight/reset_distribution_by_dynamics_band.csv
runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight/reset_distribution_by_source_kind.csv
runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight/claim_boundary.csv
```

Each reset row must preserve:

```text
task_source_id
candidate_id
candidate_set_id
branch_id
panel_task_family
source_split
source_kind
source_edge
window_tag
task_role_semantics
obstacle_distance_band
road_width_band
curvature_band
dynamics_band
initial_speed_band
same_current_constraint
history_intervention_candidate
warmup_mode
terminal_margin_bucket
materialization_semantics
proxy_template_family
generated_source_row
paper_validity_claim
```

and add reset-only fields:

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

## M2066 Pass Gates

M2066 passes only if:

```text
result_class == outcome_supported_decisive_reset_validation_preflight_pass
input_executable_spec_count == 240
target_executable_spec_count == 240
reset_attempt_count == 240
reset_success_count == 240
reset_failure_count == 0
observation_finite_count == 240
observation_dimension_failure_count == 0
obstacle_initialized_count == 240
contract_violation_count == 0
metadata_missing_count == 0
forbidden_key_violation_count == 0
family_quota_pass == true
split_quota_pass == true
difficulty_axis_coverage_pass == true
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

If any reset fails, M2066 must fail closed and route to result/failure audit. It
must not repair and rerun inside the same milestone.

## Claim Boundary

If M2066 passes, it may claim only:

```text
the M2063 240-spec outcome-supported decisive smoke-proxy panel is reset-valid
under the current simulator and strict human-view observation contract.
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
m2066-paper-route-outcome-supported-decisive-reset-validation-implementation-and-run
```
