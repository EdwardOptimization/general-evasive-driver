# M1955 Executable V2 Task-Quality Calibrated Source Materialization Design

- status: completed
- decision: `task_quality_calibrated_source_materialization_design_admit_selector_implementation`
- branch: `paper_route_task_quality_calibrated_materialization`
- parent synthesis: `docs/m1954-executable-v2-task-quality-offtrack-support-repair-branch-synthesis.md`
- source rows: `runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_source_rows.csv`
- accepted cells: `runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_accepted_cells.csv`
- reset/rollout/measured execution in M1955: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M1955 turns the M1952 calibrated source-mining pass into a bounded source
materialization design. It does not execute environment reset, rollout, measured
execution, policy actions, replay, PPO, or ranking.

The M1952 source pool is a repair-wave pool, not the complete M1925 five-tier by
four-role matrix. Therefore M1956 must not copy the older 5x4 materialization
selector. The selector should preserve repair-source diversity and calibrated
anchor provenance while creating a small executable panel:

```text
selected source count: 80
expected controller-profile count: 12
expected planned workload cells: 960
```

The 960 workload cells are only a planning target for the later materializer:
80 selected sources crossed with the current 12 support-first controller
profiles.

## M1952 Supported Source Pool

M1952 provides:

```text
input templates: 160
supported sources: 130
accepted cells: 5981
public-gate supported sources: 40
guardrail violation count: 0
```

Supported source counts by repair source kind:

```text
anchor_neighborhood: 64
success_stabilizer: 39
offtrack_boundary_relief: 11
mitigation_isolation_check: 16
```

Supported source counts by role:

```text
stable_aeb: 86
stable_aes_only: 21
unavoidable_mitigation: 14
drift_required_recovery: 9
```

Supported source-kind by role:

```text
anchor_neighborhood / stable_aeb: 64
success_stabilizer / stable_aeb: 18
success_stabilizer / stable_aes_only: 10
success_stabilizer / drift_required_recovery: 6
success_stabilizer / unavoidable_mitigation: 5
offtrack_boundary_relief / stable_aes_only: 11
mitigation_isolation_check / unavoidable_mitigation: 9
mitigation_isolation_check / stable_aeb: 4
mitigation_isolation_check / drift_required_recovery: 3
```

Calibrated anchor provenance:

```text
calibrated_anchor_fallback_used_count: 64
post_friction_step: 32
steady_surface: 32
```

## Eligibility Filter

M1956 should load only M1952 source rows satisfying:

```text
source_support_status == supported
source_split in {public_gate, public_debug}
labels_enter_actor_input == false
v2_ranking_admissible_by_default == false
profile_specific_tuning == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

The selector must fail closed if any selected row violates these guardrails.

## Selection Quotas

M1956 should select exactly 80 source rows with the following repair-source
kind quotas:

```text
anchor_neighborhood: 32
success_stabilizer: 24
offtrack_boundary_relief: 8
mitigation_isolation_check: 16
```

This intentionally down-samples the 64 anchor rows so the calibrated stable-AEB
fallback does not dominate the panel, while preserving every mitigation
isolation row and enough offtrack-relief rows to test the repaired support axis.

### Anchor Neighborhood

Select 32 calibrated anchor rows:

```text
role: stable_aeb
base_geometry_source starts with: m1950_calibrated_anchor_fallback
post_friction_step: 16
steady_surface: 16
```

This keeps both M1950 calibrated anchor surfaces represented and avoids using
uncalibrated anchor fallback geometry.

### Success Stabilizer

Select 24 success-stabilizer rows:

```text
stable_aeb: 8
  post_friction_step: 4
  steady_surface: 4

stable_aes_only: 6
  post_friction_step: 3
  steady_surface: 3

drift_required_recovery: 6
  post_friction_step: 4
  steady_surface: 2

unavoidable_mitigation: 4
  post_friction_step: 1
  steady_surface: 3
```

The resulting success-stabilizer surface split is balanced overall:

```text
post_friction_step: 12
steady_surface: 12
```

### Offtrack Boundary Relief

Select 8 supported offtrack-boundary-relief rows:

```text
repair_source_kind: offtrack_boundary_relief
role: stable_aes_only
source_split: public_gate
```

M1952 source rows have no parent surface variant for this family. The selector
should preserve the blank surface as `relief_surface_unspecified` in the output
summary rather than inventing a post/steady balance claim.

### Mitigation Isolation Check

Select all 16 supported mitigation-isolation rows:

```text
unavoidable_mitigation: 9
  post_friction_step: 4
  steady_surface: 5

stable_aeb: 4
  post_friction_step: 4

drift_required_recovery: 3
  steady_surface: 3
```

These rows are rare and are the only supported mitigation-isolation surface in
M1952, so M1956 should preserve them instead of sampling them down.

## Deterministic Selection Protocol

M1956 should implement a deterministic source-only selector:

1. Load M1952 `repair_source_rows.csv`.
2. Apply the eligibility filter.
3. Group by `repair_source_kind`, `source_role_semantics`, and normalized
   `parent_surface_variant`.
4. Select rows to satisfy the exact quota table above.
5. Prefer `public_gate` over `public_debug` only within quota buckets where
   both splits are available.
6. Within a bucket, sort stably by:

```text
accepted_cell_count descending
source_split priority: public_gate before public_debug
base_geometry_source
candidate_source_id
repair_candidate_id
```

7. Fail closed if any quota cannot be satisfied exactly.
8. Emit source-level metadata only, not controller-family rankings.

The selector should not inspect rollout outcomes, run resets, tune controller
profiles, or create policy/controller claims.

## Output Artifact Contract

M1956 should write:

```text
configs/executable_v2_task_quality_calibrated_materialization_subset_v0.json
runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/summary.json
runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/selected_sources.csv
runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/selection_failures.csv
runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/source_kind_quota_summary.csv
runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/role_surface_quota_summary.csv
runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/claim_boundary.csv
```

The config should include:

```text
scenario_quality_branch_id
source_support_parent_artifact
accepted_cells_parent_artifact
selection_protocol_version
selected_source_count
expected_controller_profile_count
expected_planned_workload_cell_count
source_kind_quotas
role_surface_quotas
selected_sources
selection_summary
guardrail_flags
```

Each selected source should preserve at least:

```text
repair_candidate_id
repair_source_kind
repair_source_family
source_split
offtrack_repair_mode
recovery_corridor_profile
parent_candidate_source_id
parent_task_source_id
parent_profile_name
parent_feasibility_tier_id
parent_source_role_semantics
parent_surface_variant
candidate_source_id
source_v1_bounded_panel_spec_id
source_scenario_spec_id
source_role_semantics
profile_name
profile_group
speed_ref
mu
friction_step_enabled
friction_step_at
accepted_cell_count
base_geometry_source
labels_enter_actor_input
v2_ranking_admissible_by_default
profile_specific_tuning
controller_family_ranking_claim_made
paper_level_claim_made
level3_self_id_claim_made
diagnostic_only_no_ranking_claim
```

## M1956 Pass Gates

M1956 should pass only if:

```text
result_class == task_quality_calibrated_materialization_selector_pass
selected_source_count == 80
expected_controller_profile_count == 12
expected_planned_workload_cell_count == 960
anchor_neighborhood_selected_count == 32
success_stabilizer_selected_count == 24
offtrack_boundary_relief_selected_count == 8
mitigation_isolation_check_selected_count == 16
calibrated_anchor_selected_count == 32
calibrated_anchor_post_friction_step_selected_count == 16
calibrated_anchor_steady_surface_selected_count == 16
success_stabilizer_post_friction_step_selected_count == 12
success_stabilizer_steady_surface_selected_count == 12
selected_supported_source_count == 80
duplicate_candidate_source_id_count == 0
labels_enter_actor_input_count == 0
ranking_admissible_by_default_count == 0
profile_specific_tuning_count == 0
guardrail_violation_count == 0
environment_reset_started == false
environment_rollout_started == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

## Interpretation Boundary

Supported by M1955:

- calibrated source materialization has an exact source-count target;
- source-kind, role, surface, and calibrated-anchor provenance quotas are
  specified;
- M1956 can implement a deterministic selector and focused tests.

Unsupported by M1955:

- reset success;
- measured execution readiness;
- rollout success;
- controller-family ranking;
- paper-level benchmark evidence;
- policy improvement;
- level3 self-identification evidence.

## Next

Next milestone:

```text
m1956-executable-v2-task-quality-calibrated-source-materialization-selector-implementation
```

M1956 should implement the deterministic selector, focused tests, and source
subset artifacts without reset, rollout, measured execution, training, replay,
PPO, ranking, or paper-level claims.
