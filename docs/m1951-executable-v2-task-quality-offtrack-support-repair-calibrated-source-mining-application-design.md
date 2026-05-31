# M1951 Executable V2 Task-Quality Offtrack Support Repair Calibrated Source-Mining Application Design

- status: completed
- decision: `task_quality_calibrated_source_mining_application_design_admit_implementation`
- branch: `paper_route_task_quality_offtrack_support_repair`
- parent calibration: `runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/selected_anchor_fallback_geometry.json`
- reset/rollout/measured execution in M1951: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M1950 found label-correct stable-AEB fallback geometry for the anchor rows that
failed in M1947. M1951 designs how to apply that calibrated fallback to the
full no-rollout source-mining adapter without hard-coding new geometry constants
or weakening any source-kind gates.

This is still source-quality plumbing. It is not reset validation, measured
execution, controller ranking, paper-level evidence, or self-identification
evidence.

## Adapter Change

M1952 should extend:

```text
src/autodrift/executable_v2_task_quality_offtrack_support_repair_source_mining.py
```

with an optional artifact input:

```text
--anchor-fallback-geometry runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/selected_anchor_fallback_geometry.json
```

The artifact must be read as data. Do not copy the selected distance or
half-width into source code as a magic constant.

The calibrated fallback should apply only when all of these are true:

```text
repair_source_kind == anchor_neighborhood
source_role_semantics == stable_aeb
sampled_obstacle_label == aeb_feasible
surface_variant in {post_friction_step, steady_surface}
no exact M1928 source geometry was resolved
```

Lookup key:

```text
tier_c_boundary_near_miss::stable_aeb::aeb_feasible::<surface_variant>
```

If the key is present, the adapter should use:

```text
speed_ref
mu
obstacle_distance
obstacle_half_width
base_track_width
```

from the calibration artifact and set:

```text
base_geometry_source = m1950_calibrated_anchor_fallback::<surface_variant>
```

All non-anchor rows and exact M1928-resolved rows must keep the M1947 behavior.

## Command

M1952 should run:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_offtrack_support_repair_source_mining \
  --repair-templates configs/executable_v2_task_quality_offtrack_support_repair_candidates_v0.json \
  --executable-task-specs runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json \
  --anchor-fallback-geometry runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/selected_anchor_fallback_geometry.json \
  --output-dir runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining \
  --next-blocker m1953-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-result-audit
```

The output schema should match M1947, with additional summary fields:

```text
anchor_fallback_geometry_path
calibrated_anchor_fallback_used_count
calibrated_anchor_fallback_used_by_surface
```

The existing `base_geometry_source` column is enough to audit which source rows
used calibrated fallback geometry.

## Pass Gates

M1952 passes only if the calibrated source-mining run satisfies the original
M1947 gates plus calibration provenance:

```text
result_class == task_quality_offtrack_support_repair_source_mining_pass
input_template_count == 160
source_candidate_count == 160
resolution_failure_count == 0
accepted_cell_count_total > 0
supported_source_count >= 64
public_gate_supported_source_count >= 24

anchor_neighborhood_supported_source_count >= 16
success_stabilizer_supported_source_count >= 16
offtrack_boundary_relief_supported_source_count >= 8
mitigation_isolation_check_source_count == 16

calibrated_anchor_fallback_used_count == 64
calibrated_anchor_fallback_used_by_surface.post_friction_step == 32
calibrated_anchor_fallback_used_by_surface.steady_surface == 32

labels_enter_actor_input_count == 0
v2_ranking_admissible_by_default_count == 0
profile_specific_tuning_count == 0
guardrail_violation_count == 0

environment_reset_started == false
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

If the calibrated run fails, M1953 should audit the failure instead of
immediately weakening thresholds. In particular, if anchor support still fails,
the branch should synthesize before another small anchor repair.

## Expected Outcome

Because M1950 calibrated both surfaces to `32/32` supported anchor rows, the
expected M1952 improvement is:

```text
anchor_neighborhood_supported_source_count: 0 -> at least 16
```

Non-anchor source-kind support should not regress materially because the
calibrated fallback applies only to anchor rows.

## Unsupported Claims

M1951 does not support:

- repaired full source-mining pass;
- reset validity;
- measured execution readiness;
- controller-family ranking;
- finite-window vs GRU conclusion;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1952-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-implementation
```

M1952 should implement the artifact input path, run the calibrated no-rollout
source-mining command, and route the result to M1953 audit.
