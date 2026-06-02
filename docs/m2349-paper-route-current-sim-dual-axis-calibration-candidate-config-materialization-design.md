# M2349 Paper-Route Current-Sim Dual-Axis Calibration Candidate Config Materialization Design

- status: completed
- result_class: `dual_axis_candidate_config_materialization_design_admit_artifact_only_implementation`
- manifest: `experiments/manifests/m2349-paper-route-current-sim-dual-axis-calibration-candidate-config-materialization-design.json`
- parent audit: `docs/m2348-paper-route-current-sim-dual-axis-redesign-calibration-materialization-result-audit.md`
- parent candidate artifacts: `runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization`
- admitted follow-up: `artifact-only candidate config-pack materializer`
- reset/rollout/policy action in M2349: `false`
- measured execution in M2349: `false`
- training/replay/PPO in M2349: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`

## Purpose

M2347 materializes 53 candidate rows from the 26-row dual-axis blocker:

```text
G candidates: 28
H candidates: 13
GH candidates: 12
```

M2348 accepts those artifacts but blocks direct validation because validating all
candidate rows or candidate combinations would create a new local-search space.
M2349 designs a bounded candidate config-pack materializer that collapses the
candidate set into a small non-ranking pack family.

## Inputs For M2350

M2350 should read:

```text
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/calibration_candidate_rows.csv
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/calibration_config_candidates.json
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/secondary_coverage_rows.csv
configs/paper_route_current_sim_scenario_task_family_v0.json
docs/m2349-paper-route-current-sim-dual-axis-calibration-candidate-config-materialization-design.md
```

M2350 must not overwrite the active config. It should write config-pack artifacts
under:

```text
runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization
```

## Config-Pack Family

M2350 should materialize exactly these pack definitions:

```text
baseline_reference_pack:
  read-only copy/provenance pointer to the current active config.
  It is not a modified pack and is not a validation result.

g_primary_pack:
  select one deterministic primary G candidate for each of the 13
  geometry/timing input rows.

h_primary_pack:
  select one deterministic primary H candidate for each of the 13 hidden-range
  input rows.

g_h_primary_pack:
  select G primary candidates for the 13 geometry/timing rows and H primary
  candidates for the 13 hidden-range rows.

gh_minimal_pack:
  use GH candidates where M2347 produced them; otherwise fall back to the
  corresponding G or H primary candidate for that scenario.
```

No other pack should be emitted in M2350. This bounds the candidate space:

```text
config_pack_count: 5
modified_config_pack_count: 4
baseline_reference_pack_count: 1
```

## Candidate Selection Rules

### G Primary

For each scenario with `source_recommended_route == geometry_timing_rebalance_candidate`,
select exactly one candidate using this priority:

```text
1. timing_step_earlier
2. lateral_offset_step_toward_centerline
3. speed_step_down
4. track_width_step_up
5. radius_step_up
```

Ties should be broken lexicographically by `candidate_id`. The output should
record `selection_rule = g_primary_priority`.

### H Primary

For each scenario with `source_recommended_route == hidden_dynamics_range_rebalance_candidate`,
select exactly one H candidate. M2347 emits one H candidate per H-row, but M2350
should still fail closed if duplicates or missing rows appear. The output should
record `selection_rule = h_primary_unique`.

### GH Minimal

For each scenario:

```text
if a GH candidate exists:
  select the first GH candidate by candidate_id
elif a G primary candidate exists:
  select the G primary candidate
elif an H primary candidate exists:
  select the H primary candidate
else:
  fail closed
```

The output should record `selection_rule = gh_minimal_prefer_gh_else_primary`.

## Patch Application Rules

M2350 should produce artifact config packs, not modify the active config. For
each selected candidate, it should copy the source scenario spec and apply the
candidate metadata consistently:

```text
obstacle_longitudinal_timing_bucket:
  update metadata; if a same-role reference spec with the after-bucket exists,
  copy its obstacle distance range; otherwise mark patch_resolution = metadata_only.

obstacle_lateral_offset_bucket:
  update metadata; centerline maps to obstacle lateral_offset_range [0.0, 0.0].
  Other after-buckets must use a reference spec or remain metadata_only.

initial_speed_mps:
  update metadata and env_config.speed_range to the selected scalar value.

track_width_m:
  update metadata and env_config.track_width to the selected scalar value.

track_radius_m:
  update metadata and env_config.track_radius to the selected scalar value.

hidden_dynamics_bucket:
  if candidate after-bucket is nominal_neighbor, copy randomization fields from
  the closest same-role nominal reference when available; otherwise mark
  patch_resolution = hidden_metadata_only.
  if candidate after-bucket is same_scene_balanced_panel, emit a balanced-panel
  metadata patch and mark patch_resolution = hidden_panel_metadata_only.
```

Patch resolution is an artifact field. It is not a validation claim. Any pack
with metadata-only patches remains ineligible for reset validation until a later
audit accepts an executable mapping route.

## Output Artifacts

M2350 should write:

```text
runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/summary.json
runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_pack_manifest.json
runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/candidate_selection_rows.csv
runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/scenario_spec_patch_rows.csv
runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/claim_boundary.csv
runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_packs/baseline_reference_pack.json
runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_packs/g_primary_pack.json
runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_packs/h_primary_pack.json
runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_packs/g_h_primary_pack.json
runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_packs/gh_minimal_pack.json
```

Required `candidate_selection_rows.csv` fields:

```text
pack_id
scenario_spec_id
candidate_id
candidate_axis
transform_name
selection_rule
selected_for_pack
diagnostic_only
ranking_admissible
winner_selected
paper_level_claim_made
level3_self_id_claim_made
scenario_redesign_executed
```

Required `scenario_spec_patch_rows.csv` fields:

```text
pack_id
scenario_spec_id
candidate_id
patch_resolution
hidden_dynamics_bucket_before
hidden_dynamics_bucket_after
timing_bucket_before
timing_bucket_after
lateral_bucket_before
lateral_bucket_after
initial_speed_mps_before
initial_speed_mps_after
track_width_m_before
track_width_m_after
track_radius_m_before
track_radius_m_after
env_config_patch_applied
metadata_only_patch
diagnostic_only
ranking_admissible
winner_selected
paper_level_claim_made
level3_self_id_claim_made
scenario_redesign_executed
```

Required summary fields:

```text
candidate_input_count
config_pack_count
modified_config_pack_count
baseline_reference_pack_count
g_primary_selection_count
h_primary_selection_count
g_h_primary_selection_count
gh_minimal_selection_count
metadata_only_patch_count
env_config_patch_count
unresolved_patch_count
active_config_overwritten
environment_reset_started
environment_rollout_started
measured_rollout_started
training_started
replay_started
ppo_used
support_policy_ranking_claim_made
controller_family_ranking_claim_made
winner_selected
paper_level_claim_made
finite_window_vs_gru_conclusion_made
level3_self_id_claim_made
scenario_redesign_executed_claim_made
guardrail_violation_count
```

## Acceptance Criteria

M2350 should pass if:

```text
candidate_input_count == 53
config_pack_count == 5
modified_config_pack_count == 4
baseline_reference_pack_count == 1
g_primary_selection_count == 13
h_primary_selection_count == 13
g_h_primary_selection_count == 26
gh_minimal_selection_count == 26
active_config_overwritten == false
guardrail_violation_count == 0
all required artifacts exist
```

M2350 should fail closed if:

```text
candidate rows cannot be grouped by source scenario;
any pack emits more than one selected candidate per scenario;
the pack family expands beyond the five allowed packs;
the active config is overwritten;
any reset, rollout, measured execution, replay, PPO, ranking, or promotion starts;
or the output claims scenario redesign has been executed.
```

## Claim Boundary

Allowed claim:

```text
M2349 designs a bounded artifact-only candidate config-pack materialization route.
```

Blocked claims:

```text
scenario redesign executed;
support-policy ranking;
controller-family comparison readiness;
residual support solved;
paper-level evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Follow-Up

Next milestone:

```text
m2350-paper-route-current-sim-dual-axis-candidate-config-materialization-implementation
```

M2350 should implement the artifact-only materializer and focused tests. It
should not run reset validation or measured execution.
