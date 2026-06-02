# M2356 Paper-Route Current-Sim Dual-Axis Candidate Pack Sampling Repair Materialization Implementation

- status: completed
- result_class: `current_sim_dual_axis_candidate_pack_sampling_repair_materialization_pass`
- manifest: `experiments/manifests/m2356-paper-route-current-sim-dual-axis-candidate-pack-sampling-repair-materialization-implementation.json`
- parent design: `docs/m2355-paper-route-current-sim-dual-axis-candidate-pack-sampling-compatible-repair-design.md`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_candidate_pack_sampling_repair.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair.py`
- output: `runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/summary.json`
- reset/rollout/policy action in M2356: `false`
- measured execution in M2356: `false`
- training/replay/PPO in M2356: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`
- reset-valid scenario pack claim made: `false`

## Command

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair.py -q

2 passed
```

M2356 ran the frozen M2355 artifact-only materializer:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_candidate_pack_sampling_repair \
  --config-pack-manifest runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_pack_manifest.json \
  --patch-rows runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/scenario_spec_patch_rows.csv \
  --candidate-selection-rows runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/candidate_selection_rows.csv \
  --reset-failure-rows runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/reset_failure_rows.csv \
  --output-dir runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair \
  --next-blocker m2357-paper-route-current-sim-dual-axis-candidate-pack-sampling-repair-result-audit
```

## Result

M2356 passes its artifact-only gates:

```text
result_class: current_sim_dual_axis_candidate_pack_sampling_repair_materialization_pass
input_config_pack_count: 5
output_config_pack_count: 5
scenario_specs_per_pack_count: 72
input_reset_failure_count: 32
baseline_env_config_fallback_count: 32
timing_related_repair_count: 27
hidden_only_repair_count: 3
lateral_hidden_repair_count: 2
repair_missing_field_count: 0
metadata_caveat_rows_preserved: true
metadata_only_patch_count: 37
metadata_patch_row_count: 78
active_config_overwritten: false
guardrail_violation_count: 0
```

Effective pack summary after fallback:

```text
baseline_reference_pack:
  original_selection_count 0
  fallback_count 0
  effective_selection_count 0

g_primary_pack:
  original_selection_count 13
  fallback_count 9
  effective_selection_count 4

h_primary_pack:
  original_selection_count 13
  fallback_count 1
  effective_selection_count 12

g_h_primary_pack:
  original_selection_count 26
  fallback_count 10
  effective_selection_count 16

gh_minimal_pack:
  original_selection_count 26
  fallback_count 12
  effective_selection_count 14
```

## Artifacts

```text
runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/summary.json
runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repaired_config_pack_manifest.json
runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repair_action_rows.csv
runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repaired_scenario_spec_patch_rows.csv
runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repaired_candidate_selection_rows.csv
runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/effective_pack_summary_rows.csv
runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repair_missing_field_rows.csv
runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/claim_boundary.csv
runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/config_packs/*.json
```

## Interpretation

Supported:

- a repaired five-pack artifact family exists;
- exactly 32 M2353 failed rows received baseline env_config fallback;
- metadata caveat reporting was preserved;
- no active config was overwritten;
- no reset, rollout, policy action, ranking, paper, or self-ID claim was made.

Unsupported:

- the repaired packs are reset-valid;
- scenario redesign has been executed;
- support-policy or controller-family ranking;
- measured driver performance;
- finite-window vs GRU result;
- level3 self-identification evidence;
- paper-level current-sim result.

## Next

Next milestone:

```text
m2357-paper-route-current-sim-dual-axis-candidate-pack-sampling-repair-result-audit
```

M2357 should audit the repaired artifact result and decide whether to design or
run a repaired-pack reset validation. It should not run reset itself.
