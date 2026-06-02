# M2355 Paper-Route Current-Sim Dual-Axis Candidate Pack Sampling-Compatible Repair Design

- status: completed
- decision: `sampling_compatible_repair_design_admit_artifact_only_materializer`
- manifest: `experiments/manifests/m2355-paper-route-current-sim-dual-axis-candidate-pack-sampling-compatible-repair-design.json`
- parent audit: `docs/m2354-paper-route-current-sim-dual-axis-candidate-pack-reset-validation-result-audit.md`
- reset/rollout/policy action in M2355: `false`
- measured execution in M2355: `false`
- training/replay/PPO in M2355: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`
- reset-valid scenario pack claim made: `false`

## Repair Goal

M2355 designs a bounded no-reset repair for the M2350 candidate packs after
M2353 failed reset validation:

```text
reset_attempt_count: 360
reset_success_count: 328
reset_failure_count: 32
dominant failure: sampling_incompatible_candidate_transform
dominant transform: late_close -> mid timing changes, 27/32 failures
baseline_reference_pack failures: 0
```

The goal is not to find a better controller or rank packs. The goal is to
materialize a repaired candidate-pack family that can be reset-validated in a
later milestone.

## Design Decision

Use row-level baseline fallback for sampler-incompatible failed rows.

For every `(pack_id, scenario_spec_id)` in the M2353 failure rows:

```text
1. locate the same scenario_spec_id in baseline_reference_pack;
2. replace the failed pack's scenario spec env_config with the baseline spec
   env_config and env-linked top-level fields;
3. preserve the failed candidate metadata in a repair audit row;
4. mark the row sampling_repair_action = baseline_env_config_fallback;
5. do not change successful modified rows.
```

This is deliberately conservative. It avoids raw candidate search, avoids
changing label filters opportunistically, and keeps M2356 artifact-only.

## Fields To Restore From Baseline

M2356 should restore these fields from the baseline spec when applying fallback:

```text
env_config
hidden_dynamics_bucket
friction_bucket
mu_range
brake_scale_bucket
brake_scale_range
actuator_lag_bucket
steer_tau_scale_range
drive_tau_scale_range
front_tire_stiffness_scale_range
rear_tire_stiffness_scale_range
obstacle_longitudinal_timing_bucket
obstacle_longitudinal_distance_m
obstacle_lateral_offset_bucket
obstacle_lateral_offset_m
obstacle_half_width_m
finish_on_pass
```

If a field is absent in either baseline or candidate pack, M2356 should record
it in `repair_missing_field_rows.csv` and fail closed if the missing field would
make the env config ambiguous.

## Expected Repair Scope

From M2354:

```text
failed rows total: 32
g_primary_pack: 9
h_primary_pack: 1
g_h_primary_pack: 10
gh_minimal_pack: 12
baseline_reference_pack: 0
```

Expected repair actions:

```text
baseline_env_config_fallback_count: 32
timing_related_repair_count: 27
hidden_only_repair_count: 3
lateral_hidden_repair_count: 2
```

Expected effective modified selection counts after fallback:

```text
g_primary_pack: 4 effective modified rows, 9 fallback rows
h_primary_pack: 12 effective modified rows, 1 fallback row
g_h_primary_pack: 16 effective modified rows, 10 fallback rows
gh_minimal_pack: 14 effective modified rows, 12 fallback rows
baseline_reference_pack: unchanged
```

These counts are not performance claims. They only quantify how much of each
candidate pack remains materially modified after making failed rows
sampling-compatible.

## Rejected Alternatives

Rejected for M2356:

```text
increase max_sample_attempts:
  This could hide infeasible labels and make reset validity seed-dependent.

expand allowed_labels:
  This changes role semantics and can silently make hard rows easier.

change only top-level metadata:
  M2353 failures occur during actual env reset, so metadata-only repair is not
  enough.

raw candidate search:
  This reopens local search and violates the five-pack bounded route.

direct reset rerun:
  M2355 is design-only; M2356 should materialize repaired artifacts first.
```

## M2356 Materializer Contract

M2356 should implement:

```text
autodrift.paper_route_current_sim_dual_axis_candidate_pack_sampling_repair
```

Inputs:

```text
M2350 config_pack_manifest.json
M2350 scenario_spec_patch_rows.csv
M2350 candidate_selection_rows.csv
M2353 reset_failure_rows.csv
```

Outputs:

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

M2356 pass gates:

```text
result_class == current_sim_dual_axis_candidate_pack_sampling_repair_materialization_pass
input_config_pack_count == 5
output_config_pack_count == 5
scenario_specs_per_pack_count == 72
input_reset_failure_count == 32
baseline_env_config_fallback_count == 32
timing_related_repair_count == 27
hidden_only_repair_count == 3
lateral_hidden_repair_count == 2
repair_missing_field_count == 0
metadata_caveat_rows_preserved == true
active_config_overwritten == false
guardrail_violation_count == 0
```

M2356 must not run reset validation. M2357 should be a separate reset-only
validation design or implementation depending on the M2356 result audit.

## Claim Boundary

M2355 supports only:

```text
a bounded sampling-compatible repair design exists.
```

M2355 does not support:

```text
repaired packs are reset-valid;
scenario redesign has been executed;
rollout success;
support-policy ranking;
controller-family ranking;
paper-level benchmark evidence;
finite-window vs GRU result;
level3 self-identification evidence.
```

## Next

Next milestone:

```text
m2356-paper-route-current-sim-dual-axis-candidate-pack-sampling-repair-materialization-implementation
```

M2356 should implement the artifact-only materializer and focused tests. It
must not run reset validation.
