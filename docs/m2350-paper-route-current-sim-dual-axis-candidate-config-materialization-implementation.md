# M2350 Paper-Route Current-Sim Dual-Axis Candidate Config Materialization Implementation

- status: completed
- result_class: `current_sim_dual_axis_candidate_config_materialization_pass`
- manifest: `experiments/manifests/m2350-paper-route-current-sim-dual-axis-candidate-config-materialization-implementation.json`
- parent design: `docs/m2349-paper-route-current-sim-dual-axis-calibration-candidate-config-materialization-design.md`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_candidate_config_materialization.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_candidate_config_materialization.py`
- output: `runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/summary.json`
- reset/rollout/policy action in M2350: `false`
- measured execution in M2350: `false`
- training/replay/PPO in M2350: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_candidate_config_materialization \
  --candidate-dir runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization \
  --config configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization
```

Focused validation:

```text
PYTHONPATH=src python -m pytest tests/test_paper_route_current_sim_dual_axis_candidate_config_materialization.py -q
1 passed

python -m compileall -q src tests
passed
```

## Output Artifacts

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

## Result Summary

M2350 materializes the bounded five-pack family:

```text
result_class: current_sim_dual_axis_candidate_config_materialization_pass
candidate_input_count: 53
config_pack_count: 5
modified_config_pack_count: 4
baseline_reference_pack_count: 1
g_primary_selection_count: 13
h_primary_selection_count: 13
g_h_primary_selection_count: 26
gh_minimal_selection_count: 26
active_config_overwritten: false
guardrail_violation_count: 0
```

Patch provenance:

```text
env_config_patch_count: 78
metadata_only_patch_count: 37
unresolved_patch_count: 0
```

The metadata-only caveat is expected for hidden-dynamics bucket labels such as
`nominal_neighbor` and `same_scene_balanced_panel`. M2350 does not claim these
packs are reset-valid. It only materializes bounded artifacts for later audit.

## Interpretation

M2350 converts the raw 53-row candidate set into a controlled pack family:

```text
baseline_reference_pack: selection_count 0
g_primary_pack: selection_count 13
h_primary_pack: selection_count 13
g_h_primary_pack: selection_count 26
gh_minimal_pack: selection_count 26
```

This prevents candidate-combination explosion and keeps the next step auditable.
The active config remains untouched.

## Claim Boundary

Allowed claim:

```text
M2350 materializes artifact-only candidate config-pack files.
```

Blocked claims:

```text
scenario redesign executed;
reset-valid redesigned scenario pack;
support-policy ranking;
controller-family comparison readiness;
residual support solved;
paper-level evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Follow-Up

M2351 should synthesize the dual-axis calibration branch, especially the
metadata-only patch caveat, before any reset validation design:

```text
experiments/manifests/m2351-paper-route-current-sim-dual-axis-calibration-branch-synthesis.json
```
