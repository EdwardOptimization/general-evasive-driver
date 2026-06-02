# M2359 Paper-Route Current-Sim Dual-Axis Repaired Pack Reset Validation Implementation

- status: completed
- result_class: `current_sim_dual_axis_repaired_pack_reset_validation_pass`
- manifest: `experiments/manifests/m2359-paper-route-current-sim-dual-axis-repaired-pack-reset-validation-implementation.json`
- summary: `runs/m2359_paper_route_current_sim_dual_axis_repaired_pack_reset_validation/summary.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_repaired_pack_reset_validation.py`
- focused tests: `3 passed`
- reset/rollout distinction: reset only
- environment rollout in M2359: `false`
- policy action executed: `false`
- measured execution in M2359: `false`
- training/replay/PPO: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`
- reset-valid repaired pack claim made in artifact: `false`

## Result

M2359 implements and runs the frozen M2358 repaired-pack reset-only validator
over the five M2356 repaired candidate config packs:

```text
input_config_pack_count: 5
scenario_specs_per_pack_count: 72
reset_attempt_count: 360
reset_success_count: 360
reset_failure_count: 0
observation_finite_count: 360
observation_dimension_failure_count: 0
obstacle_initialized_count: 360
contract_violation_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
```

The repaired pack family is reset-valid under the current simulator and the
strict human-view observation contract.

## Repair Metadata Preservation

M2359 preserves the M2356 repair-action metadata through reset rows:

```text
baseline_env_config_fallback_count: 32
repair_action_row_count: 32
repair_action_reset_row_count: 32
repair_action_rows_preserved: true
repair_class_counts:
  timing_related: 27
  hidden_only: 3
  lateral_hidden: 2
metadata_caveat_row_count: 78
metadata_only_patch_count: 37
metadata_caveat_rows_preserved: true
unresolved_patch_count: 0
```

Effective modified selections remain:

```text
g_primary_pack: 4
h_primary_pack: 12
g_h_primary_pack: 16
gh_minimal_pack: 14
```

## Artifacts

M2359 writes:

```text
runs/m2359_paper_route_current_sim_dual_axis_repaired_pack_reset_validation/summary.json
runs/m2359_paper_route_current_sim_dual_axis_repaired_pack_reset_validation/reset_rows.csv
runs/m2359_paper_route_current_sim_dual_axis_repaired_pack_reset_validation/reset_failure_rows.csv
runs/m2359_paper_route_current_sim_dual_axis_repaired_pack_reset_validation/pack_summary_rows.csv
runs/m2359_paper_route_current_sim_dual_axis_repaired_pack_reset_validation/repair_action_reset_rows.csv
runs/m2359_paper_route_current_sim_dual_axis_repaired_pack_reset_validation/contract_rows.csv
runs/m2359_paper_route_current_sim_dual_axis_repaired_pack_reset_validation/metadata_caveat_rows.csv
runs/m2359_paper_route_current_sim_dual_axis_repaired_pack_reset_validation/claim_boundary.csv
```

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_dual_axis_repaired_pack_reset_validation.py
```

Result:

```text
3 passed in 2.10s
```

Frozen reset-only command:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_repaired_pack_reset_validation \
  --repaired-config-pack-manifest runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repaired_config_pack_manifest.json \
  --repair-action-rows runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repair_action_rows.csv \
  --repaired-patch-rows runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repaired_scenario_spec_patch_rows.csv \
  --effective-pack-summary-rows runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/effective_pack_summary_rows.csv \
  --output-dir runs/m2359_paper_route_current_sim_dual_axis_repaired_pack_reset_validation \
  --eval-seed-base 235900 \
  --target-pack-count 5 \
  --target-scenario-specs-per-pack 72 \
  --expected-observation-dim 72 \
  --next-blocker m2360-paper-route-current-sim-dual-axis-repaired-pack-reset-validation-result-audit
```

## Claim Boundary

M2359 supports only this claim:

```text
the five M2356 repaired candidate config packs are reset-valid under the
current simulator and strict human-view observation contract.
```

It does not support:

```text
scenario redesign executed;
rollout success;
measured execution success;
support-policy ranking;
controller-family ranking;
paper-level benchmark evidence;
finite-window vs GRU result;
level3 self-identification evidence.
```

## Decision

Decision:

```text
repaired_pack_reset_validation_pass_route_to_result_audit
```

M2360 should audit the M2359 pass before any measured-execution design. It
should verify the claim boundary and decide whether the next paper-route step is
a bounded measured execution design or another task-quality check.
