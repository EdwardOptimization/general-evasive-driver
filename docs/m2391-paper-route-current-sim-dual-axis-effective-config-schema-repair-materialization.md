# M2391 Paper-Route Current-Sim Dual-Axis Effective Config Schema Repair Materialization

- status: completed
- result class: `current_sim_dual_axis_effective_config_schema_repair_materialization_pass`
- manifest: `experiments/manifests/m2391-paper-route-current-sim-dual-axis-effective-config-schema-repair-materialization.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization.py`
- focused tests: `2 passed`
- summary: `runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/summary.json`
- candidate source: `runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation`
- base pack manifest: `runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repaired_config_pack_manifest.json`
- environment load/reset/step in M2391: `0/0/0`
- policy action in M2391: `false`
- repair execution/training/replay/PPO: `false`
- active config overwrite: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Result Summary

M2391 implemented and ran the artifact-only effective candidate pack
materializer designed in M2390. It joined M2385 overlay candidates to M2356
reset-valid repaired pack scenario specs by `source_slice_axis/source_slice_value`.

```text
source_candidate_config_count: 54
static_validation_pass_count: 54
static_validation_failure_count: 0
effective_candidate_config_written_count: 54
effective_candidate_config_outside_run_dir_count: 0
candidate_without_matching_scenarios_count: 0
candidate_without_env_config_count: 0
actor_contract_violation_count: 0
base_pack_count: 5
base_scenario_specs_per_pack_count: 72
selected_scenario_reference_count: 2049
min_selected_scenario_count: 6
max_selected_scenario_count: 180
guardrail_violation_count: 0
failure_types_observed: []
```

Base scenario counts:

```text
baseline_reference_pack: 72
g_primary_pack: 72
h_primary_pack: 72
g_h_primary_pack: 72
gh_minimal_pack: 72
```

Candidate repair families:

```text
priority_offtrack_containment_repair: 26
offtrack_containment_repair: 10
guarded_offtrack_containment_repair: 18
```

Source slice axes:

```text
hidden_dynamics_bucket: 4
obstacle_lateral_offset_bucket: 2
obstacle_longitudinal_timing_bucket: 1
role_family: 4
role_family+hidden_dynamics_bucket: 15
role_family+obstacle_lateral_offset_bucket: 10
role_family+obstacle_longitudinal_timing_bucket: 11
sampled_obstacle_label: 3
scenario_family_id: 4
```

## Artifacts

M2391 wrote:

```text
runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/summary.json
runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_config_materialization_manifest.json
runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_config_rows.csv
runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_scenario_rows.csv
runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/claim_boundary.csv
runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_configs/*.json
```

The `effective_candidate_scenario_rows.csv` has 2049 data rows plus header.
The run directory contains 54 effective candidate config JSON files plus the
summary/manifest/CSV artifacts.

## Supported Claims

M2391 supports these bounded claims:

- The M2390 schema correction is executable as artifact-only materialization.
- All 54 M2385 candidate overlays can be joined to at least one M2356
  reset-valid base scenario spec.
- The generated effective candidate pack artifacts stay under the M2391 run
  directory.
- Selected base scenario specs preserve the P0 human-view no-wheel no-oracle
  actor contract guardrails.
- No active config overwrite, environment load/reset/step, policy action,
  repair execution, training, ranking, or forbidden paper/self-ID/current-sim
  claim occurred.

## Blocked Claims

M2391 still blocks:

```text
reset compatibility of effective candidate artifacts
rollout or measured execution
repair execution
training repair success
support-policy or controller-family ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
scenario redesign executed
current-sim verdict
```

## Decision

Decision:

```text
effective_candidate_pack_materialization_pass_route_to_branch_synthesis
```

Next milestone:

```text
m2392-paper-route-current-sim-dual-axis-effective-config-materialization-branch-synthesis
```

M2392 should synthesize M2387-M2391 before another narrow validation-design
step, then decide whether to adapt reset validation to effective candidate pack
artifacts. It should not rerun materialization, reset environments, execute
repair, train, rank, or make paper/self-ID/current-sim claims.
