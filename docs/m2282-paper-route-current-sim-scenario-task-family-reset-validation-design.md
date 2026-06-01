# M2282 Paper-Route Current-Sim Scenario Task-Family Reset-Validation Design

- status: completed
- decision: `current_sim_scenario_task_family_reset_validation_design_route_to_branch_synthesis_before_implementation`
- manifest: `experiments/manifests/m2282-paper-route-current-sim-scenario-task-family-reset-validation-design.json`
- input config: `configs/paper_route_current_sim_scenario_task_family_v0.json`
- reset execution in M2282: `false`
- rollout/measured execution in M2282: `false`
- policy actions executed in M2282: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2282 freezes a reset-only validation layer for the refreshed scenario
task-family config pack. It does not run reset. Because the branch has reached
the workflow synthesis cadence, the next milestone must synthesize M2273-M2282
before implementation. A later implementation milestone may run reset-only
validation if it uses the exact command and fail-closed gates below.

Target:

```text
input scenario specs: 72
reset attempts: 72
expected observation dimension: 72
rollout steps: 0
policy actions: 0
```

## Validator Decision

Implement a focused validator:

```text
autodrift.paper_route_current_sim_scenario_task_family_reset_validation
```

Do not reuse the executable-v2 validators directly. Their reset mechanics are
useful, but their schema is tied to `executable_task_specs`, feasibility tiers,
source roles, and older surface variants. The M2280/M2281 pack is a
`scenario_specs` config with role-family, timing, lateral-offset, hidden
dynamics, and claim-boundary metadata that must be preserved in reset rows.

## Frozen Reset-Validation Command

A later implementation milestone should run exactly:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_scenario_task_family_reset_validation.py

PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_reset_validation \
  --config configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation \
  --eval-seed-base 228300 \
  --target-spec-count 72 \
  --expected-observation-dim 72 \
  --next-blocker m2285-paper-route-current-sim-scenario-task-family-reset-validation-result-audit
```

## Expected Artifacts

A later implementation milestone must write:

```text
runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/summary.json
runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/reset_validation_rows.csv
runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/reset_failures.csv
runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/contract_rows.csv
runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/label_consistency_rows.csv
runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/lateral_offset_consistency_rows.csv
runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/role_family_reset_aggregate.csv
runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/scenario_family_reset_aggregate.csv
runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/obstacle_lateral_offset_bucket_reset_aggregate.csv
runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/hidden_dynamics_bucket_reset_aggregate.csv
runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/claim_boundary.csv
```

Each reset row must preserve:

```text
scenario_spec_id
scenario_family_id
role_family
role_semantics
same_scene_group_id
sampled_obstacle_label
allowed_labels_metadata_only
hidden_dynamics_bucket
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_m
obstacle_lateral_offset_bucket
initial_speed_mps
track_kind
track_radius_m
track_width_m
eval_seed
reset_success
observation_length
expected_observation_length
observation_dimension_matches
observation_finite
obstacle_initialized
actual_obstacle_label
actual_obstacle_distance
actual_obstacle_half_width
actual_obstacle_lateral_offset
environment_reset_started
environment_rollout_started
policy_action_executed
```

## Contract Checks

For every scenario spec, the reset-validation implementation must verify:

```text
history_length == 1
action_history_mode == full
include_privileged_params == false
wheel_observation_mode == none
obstacle_relative_velocity_mode == zero
labels_enter_actor_input == false
ranking_admissible == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

Violations must be written to `contract_rows.csv` and counted in
`summary.json`.

## Label Consistency Checks

The reset-validation implementation should treat labels as metadata and sampler
diagnostics only. They must not enter actor input.

Pass rules:

```text
actual_obstacle_label is in allowed_labels_metadata_only
single-label specs match sampled_obstacle_label exactly
multi-label specs may sample any allowed label
```

Counters:

```text
label_not_allowed_count
single_label_exact_mismatch_count
labels_enter_actor_input_count
```

## Lateral-Offset Consistency Checks

The reset-validation implementation must validate both numeric offset and
bucket semantics. The convention from M2279/M2280 is:

```text
positive obstacle_lateral_offset -> frame-left
negative obstacle_lateral_offset -> frame-right
centerline -> near zero
```

Pass rules:

```text
abs(actual_obstacle_lateral_offset - obstacle_lateral_offset_m) <= 0.05
centerline bucket has abs(actual offset) <= 0.05
left_offset bucket has actual offset >= +0.5
right_offset bucket has actual offset <= -0.5
```

The design intentionally includes this sign gate. During design inspection, the
current materializer constants appear to map:

```text
left_offset -> -1.2
right_offset -> +1.2
```

while the instrumentation semantics define positive as frame-left. The
implementation must fail closed if the refreshed config pack violates the
signed bucket convention. Do not silently reinterpret bucket names, and do not
repair materialization inside the same milestone.

Counters:

```text
lateral_offset_numeric_mismatch_count
lateral_bucket_mismatch_count
```

## Reset-Validation Pass Gates

A later implementation milestone passes only if:

```text
result_class == current_sim_scenario_task_family_reset_validation_pass
input_scenario_spec_count == 72
target_scenario_spec_count == 72
reset_attempt_count == 72
reset_success_count == 72
reset_failure_count == 0
observation_finite_count == 72
observation_dimension_failure_count == 0
obstacle_initialized_count == 72
actor_contract_violation_count == 0
labels_enter_actor_input_count == 0
ranking_admissible_count == 0
label_not_allowed_count == 0
single_label_exact_mismatch_count == 0
lateral_offset_numeric_mismatch_count == 0
lateral_bucket_mismatch_count == 0
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
controller_family_ranking_claim_made == false
winner_selected == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

If any reset, contract, label, or lateral-bucket check fails, the implementation
must fail closed and route to M2285 result/failure audit. It must not repair and
rerun inside the same milestone.

## Failure Taxonomy

The reset-validation implementation should classify failures as:

```text
config_schema_incompatible
env_config_build_failure
reset_sampling_failure
observation_contract_failure
human_view_contract_violation
label_metadata_inconsistency
lateral_offset_metadata_inconsistency
guardrail_violation
```

These failures are scenario-quality evidence, not controller-family evidence.

## Claim Boundary

If the implementation passes, it may claim only:

```text
the 72-spec role-family scenario pack is reset-valid under the current
simulator and strict P0 human-view observation contract.
```

It still cannot claim:

- rollout success;
- measured execution success;
- training result;
- controller-family ranking;
- winner selection;
- finite-window vs GRU comparison;
- level3 self-identification;
- paper-level benchmark evidence.

## Next

Next milestone:

```text
m2283-paper-route-current-sim-scenario-task-quality-redesign-branch-synthesis
```

M2283 must synthesize M2273-M2282 and decide whether to continue to the frozen
reset-validation implementation route, pivot to materialization repair, or stop
for review. It must not run reset.
