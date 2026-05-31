# M1946 Executable V2 Task-Quality Offtrack Support Repair Source-Mining Design

- status: completed
- decision: `task_quality_offtrack_support_repair_source_mining_design_admit_adapter_implementation`
- branch: `paper_route_task_quality_offtrack_support_repair`
- template artifact: `configs/executable_v2_task_quality_offtrack_support_repair_candidates_v0.json`
- reset/rollout/measured execution in M1946: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M1945 created a deterministic 160-row no-rollout repair template artifact. The
template rows encode repair intent and metadata, but they are not yet
source-quality evidence. M1946 defines the source-mining/preflight adapter that
must run before any reset validation or measured execution.

This is still task-quality work. It is not a controller comparison.

## Existing Helper Review

`src/autodrift/executable_v2_support_first_source_mining.py` has useful
source-mining concepts:

```text
obstacle_distance_min / max / count
obstacle_half_width_min / max / count
accepted_cells
materialization_admissible
supported_source_count
claim_boundary
```

But M1945 templates are not direct inputs to that helper. They carry:

```text
parent source metadata
repair_source_kind
obstacle_distance_delta
obstacle_half_width_delta
post_obstacle_track_width_delta
reaction_distance_delta
offtrack_repair_mode
```

Therefore M1947 should implement a focused adapter. It may reuse small
source-mining primitives if they fit, but it must not drop M1945 metadata or
silently coerce the template schema into an older support-first schema.

## Input Artifacts

M1947 should read:

```text
configs/executable_v2_task_quality_offtrack_support_repair_candidates_v0.json
runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json
```

The M1928 executable specs are needed to recover absolute base geometry when a
repair template references a measured source row. Some M1945
`anchor_neighborhood` rows are slice-level anchors rather than exact source
rows; those must use tier/role/surface default geometry defined by this design.

## Geometry Resolution

For each repair candidate, M1947 should resolve base geometry by this order:

```text
1. exact task_source_id match in M1928 executable_task_specs
2. exact candidate_source_id/source_v1_bounded_panel_spec_id match if present
3. tier/role/surface/sampled-label default geometry fallback
4. fail closed and write resolution_failure_rows.csv
```

Fallback defaults for slice-level anchors:

```text
tier_c_boundary_near_miss / stable_aeb / aeb_feasible:
  speed_ref: 18.0
  mu: 0.40
  obstacle_distance: 28.0
  obstacle_half_width: 0.80
  base_track_width: 5.75

other tier B/C/D repair rows:
  speed_ref: template speed_ref
  mu: template mu
  obstacle_distance: 30.0
  obstacle_half_width: 0.90
  base_track_width: 6.00

tier_e_mitigation_only:
  speed_ref: template speed_ref
  mu: template mu
  obstacle_distance: 22.0
  obstacle_half_width: 1.20
  base_track_width: 5.25
```

These defaults are artifact-generation defaults only. They do not enter actor
input.

## Source-Mining Mapping

Each M1945 repair template should map to one source-mining candidate row:

```text
source_candidate_id = repair_candidate_id
source_family_id = repair_source_family
source_kind = repair_source_kind
source_split = public_debug or public_gate

obstacle_distance_center =
  base_obstacle_distance + obstacle_distance_delta

obstacle_half_width_center =
  max(0.10, base_obstacle_half_width + obstacle_half_width_delta)

post_obstacle_track_width =
  base_track_width + post_obstacle_track_width_delta
```

Scan windows:

```text
anchor_neighborhood:
  obstacle_distance_center +/- 4.0, count 9
  obstacle_half_width_center +/- 0.15, count 7

success_stabilizer:
  obstacle_distance_center +/- 2.0, count 7
  obstacle_half_width_center +/- 0.10, count 5

offtrack_boundary_relief:
  obstacle_distance_center +/- 5.0, count 11
  obstacle_half_width_center +/- 0.20, count 7

mitigation_isolation_check:
  obstacle_distance_center +/- 2.0, count 5
  obstacle_half_width_center +/- 0.15, count 5
```

The adapter should preserve all M1945 metadata into output rows, especially:

```text
repair_source_kind
source_split
parent_* fields
offtrack_repair_mode
recovery_corridor_profile
```

## Output Schema

M1947 should write:

```text
runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/summary.json
runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/repair_source_rows.csv
runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/repair_accepted_cells.csv
runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/repair_blocked_rows.csv
runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/resolution_failure_rows.csv
runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/source_kind_aggregate.csv
runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/split_aggregate.csv
runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/claim_boundary.csv
```

The source rows should report:

```text
accepted_cell_count
materialization_admissible
support_status
min_accepted_cells
accepted_distance_min / max
accepted_half_width_min / max
post_obstacle_track_width
labels_enter_actor_input=false
v2_ranking_admissible_by_default=false
profile_specific_tuning=false
controller_family_ranking_claim_made=false
paper_level_claim_made=false
level3_self_id_claim_made=false
```

## Pass Gates

M1947 source-mining/preflight passes only if:

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

Passing M1947 admits only a result audit or materialization design. It still
does not admit controller ranking.

## Failure Handling

If M1947 fails because resolution failures are nonzero, repair the mapping
schema rather than relaxing gates.

If M1947 fails because supported-source count is low, route to result audit.
Possible outcomes:

```text
template support insufficient:
  redesign templates or return to broader scenario redesign.

support exists only in public_debug:
  do not proceed to measured execution; rebalance public_gate sources.

support exists but offtrack relief rows fail:
  audit whether repair deltas are too weak or geometry defaults are wrong.
```

## Claim Boundary

M1946 supports only:

```text
a source-mining/preflight design exists for M1945 repair templates.
```

It does not support:

- source repair success;
- reset validity;
- measured execution readiness;
- controller-family ranking;
- finite-window vs GRU conclusion;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1947-executable-v2-task-quality-offtrack-support-repair-source-mining-adapter-implementation
```

M1947 should implement the adapter, focused tests, and the no-rollout
source-mining run. It must not run reset, rollout, measured execution,
training, replay, PPO, profile tuning, ranking, paper-level claims, or level3
self-ID tests.
