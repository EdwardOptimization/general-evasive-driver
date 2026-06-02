# M2353 Paper-Route Current-Sim Dual-Axis Candidate Pack Reset Validation Implementation

- status: failed
- decision: `candidate_pack_reset_validation_fail_route_to_result_audit`
- manifest: `experiments/manifests/m2353-paper-route-current-sim-dual-axis-candidate-pack-reset-validation-implementation.json`
- parent design: `docs/m2352-paper-route-current-sim-dual-axis-candidate-pack-reset-validation-design.md`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_candidate_pack_reset_validation.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_candidate_pack_reset_validation.py`
- summary: `runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/summary.json`
- environment reset started: `true`
- environment rollout started: `false`
- policy action executed: `false`
- measured execution started: `false`
- training/replay/PPO: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`
- reset-valid scenario pack claim made: `false`

## Command

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_dual_axis_candidate_pack_reset_validation.py

4 passed
```

M2353 ran the frozen M2352 reset-only command:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_candidate_pack_reset_validation \
  --config-pack-manifest runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_pack_manifest.json \
  --patch-rows runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/scenario_spec_patch_rows.csv \
  --output-dir runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation \
  --eval-seed-base 235300 \
  --target-pack-count 5 \
  --target-scenario-specs-per-pack 72 \
  --expected-observation-dim 72 \
  --next-blocker m2354-paper-route-current-sim-dual-axis-candidate-pack-reset-validation-result-audit
```

## Result

M2353 fails closed because 32 of 360 reset attempts cannot sample an obstacle
scenario matching the configured filters.

```text
result_class: current_sim_dual_axis_candidate_pack_reset_validation_fail
input_config_pack_count: 5
target_config_pack_count: 5
scenario_specs_per_pack_count: 72
reset_attempt_count: 360
reset_success_count: 328
reset_failure_count: 32
observation_finite_count: 328
observation_dimension_failure_count: 0
obstacle_initialized_count: 328
contract_violation_count: 0
forbidden_key_violation_count: 0
metadata_caveat_row_count: 78
metadata_caveat_rows_preserved: true
env_config_patch_count: 78
metadata_only_patch_count: 37
unresolved_patch_count: 0
active_config_overwritten: false
guardrail_violation_count: 0
```

Pack reset success counts:

```text
baseline_reference_pack: 72 / 72
g_primary_pack: 63 / 72
h_primary_pack: 71 / 72
g_h_primary_pack: 62 / 72
gh_minimal_pack: 60 / 72
```

Pack failure counts:

```text
g_primary_pack: 9
h_primary_pack: 1
g_h_primary_pack: 10
gh_minimal_pack: 12
baseline_reference_pack: 0
```

Failure type:

```text
RuntimeError: 32
error_message: failed to sample an obstacle scenario matching the configured filters
```

The failures repeat across these scenario IDs:

```text
m2277_r2_02: 3
m2277_r2_05: 3
m2277_r2_08: 3
m2277_r3_02: 3
m2277_r3_05: 3
m2277_r3_11: 3
m2277_r5_01: 3
m2277_r5_09: 3
m2277_r5_10: 3
m2277_r5_11: 3
m2277_r5_06: 1
m2277_r5_07: 1
```

## Interpretation

Supported:

- the reset validator implementation is test-covered and produces the required
  pack, contract, metadata caveat, failure, and claim-boundary artifacts;
- the baseline reference pack resets cleanly;
- the M2350 metadata caveat is preserved exactly;
- the failure is not an actor-contract, forbidden-key, active-config overwrite,
  ranking, rollout, policy-action, or guardrail violation.

Unsupported:

- the five candidate packs are reset-valid;
- scenario redesign has been executed;
- measured rollout or controller comparison can start;
- support-policy or controller-family ranking;
- paper-level current-sim evidence;
- finite-window vs GRU or level3 self-ID conclusions.

## Failure Taxonomy

Primary failure type:

```text
scenario_sampling_failure
```

Secondary context:

```text
candidate pack schema and human-view contract are clean;
metadata caveat preservation is clean;
failures are concentrated in modified packs and repeated scenario IDs;
baseline pack has zero reset failures.
```

M2353 must not repair and rerun inside this milestone. M2354 should audit
whether the failures are caused by geometry/timing transforms, hidden-range
metadata/patch interactions, seed-source sampling, or a validator/schema
assumption.

## Artifacts

```text
runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/summary.json
runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/reset_rows.csv
runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/reset_failure_rows.csv
runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/pack_summary_rows.csv
runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/contract_rows.csv
runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/metadata_caveat_rows.csv
runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/claim_boundary.csv
```

## Next

Next milestone:

```text
m2354-paper-route-current-sim-dual-axis-candidate-pack-reset-validation-result-audit
```

M2354 should audit the fail-closed reset result before any patch repair,
sampling repair, measured execution design, or controller comparison.
