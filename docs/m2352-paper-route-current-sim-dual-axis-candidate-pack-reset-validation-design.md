# M2352 Paper-Route Current-Sim Dual-Axis Candidate Pack Reset Validation Design

- status: completed
- decision: `candidate_pack_reset_validation_design_admit_reset_only_implementation`
- manifest: `experiments/manifests/m2352-paper-route-current-sim-dual-axis-candidate-pack-reset-validation-design.json`
- parent synthesis: `docs/m2351-paper-route-current-sim-dual-axis-calibration-branch-synthesis.md`
- parent pack manifest: `runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_pack_manifest.json`
- reset/rollout/policy action in M2352: `false`
- measured execution in M2352: `false`
- training/replay/PPO in M2352: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`
- reset-valid scenario pack claim made: `false`

## Design Goal

M2352 freezes the reset-only validation route for the five M2350 candidate
config packs. It does not run reset validation. M2353 may run reset validation
only if it follows the exact workload and claim boundary below.

Target workload:

```text
config_pack_count: 5
scenario_specs_per_pack: 72
reset_attempt_count: 360
rollout_steps: 0
policy_actions: 0
expected_observation_dim: 72
```

The reset workload validates the full pack identity, not only changed rows.
The changed-row patch metadata remains a required side table for caveat
reporting.

## Pack List

M2353 must load the five packs from the M2350 manifest:

```text
baseline_reference_pack:
  path: runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_packs/baseline_reference_pack.json
  scenario_specs: 72
  selection_count: 0

g_primary_pack:
  path: runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_packs/g_primary_pack.json
  scenario_specs: 72
  selection_count: 13

h_primary_pack:
  path: runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_packs/h_primary_pack.json
  scenario_specs: 72
  selection_count: 13

g_h_primary_pack:
  path: runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_packs/g_h_primary_pack.json
  scenario_specs: 72
  selection_count: 26

gh_minimal_pack:
  path: runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_packs/gh_minimal_pack.json
  scenario_specs: 72
  selection_count: 26
```

The implementation must fail closed if any pack is missing, if any pack has a
scenario count other than 72, or if the manifest does not contain exactly five
packs.

## Metadata Caveat Reporting

M2350 reports:

```text
env_config_patch_count: 78
metadata_only_patch_count: 37
unresolved_patch_count: 0
```

M2353 must preserve this caveat explicitly. It should read:

```text
runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/scenario_spec_patch_rows.csv
```

and emit a metadata caveat artifact with at least:

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
env_config_patch_applied
metadata_only_patch
diagnostic_only
ranking_admissible
winner_selected
paper_level_claim_made
level3_self_id_claim_made
scenario_redesign_executed
```

The reset validator must not interpret metadata-only rows as executed scenario
redesign. It should only report whether the full pack resets under the current
simulator and human-view actor contract.

## M2353 Command

M2353 should implement and run exactly this reset-only command:

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

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_dual_axis_candidate_pack_reset_validation.py
```

## Expected Artifacts

M2353 must write:

```text
runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/summary.json
runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/reset_rows.csv
runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/reset_failure_rows.csv
runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/pack_summary_rows.csv
runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/contract_rows.csv
runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/metadata_caveat_rows.csv
runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/claim_boundary.csv
```

Each reset row must include:

```text
pack_id
pack_path
scenario_index
scenario_spec_id
eval_seed
reset_success
observation_length
observation_finite
observation_dimension_matches_expected
obstacle_initialized
contract_violation_count
environment_reset_started
environment_rollout_started
policy_action_executed
measured_rollout_started
training_started
replay_started
ppo_used
promoted
private_holdout_used
actor_input_contract_changed
profile_specific_tuning
controller_family_ranking_claim_made
support_policy_ranking_claim_made
paper_level_claim_made
finite_window_vs_gru_conclusion_made
level3_self_id_claim_made
scenario_redesign_executed_claim_made
reset_valid_scenario_pack_claim_made
```

## Pass Gates

M2353 passes only if:

```text
result_class == current_sim_dual_axis_candidate_pack_reset_validation_pass
input_config_pack_count == 5
target_config_pack_count == 5
scenario_specs_per_pack_count == 72
reset_attempt_count == 360
reset_success_count == 360
reset_failure_count == 0
observation_finite_count == 360
observation_dimension_failure_count == 0
obstacle_initialized_count == 360
contract_violation_count == 0
metadata_only_patch_count == 37
unresolved_patch_count == 0
metadata_caveat_rows_preserved == true
active_config_overwritten == false
guardrail_violation_count == 0
environment_reset_started == true
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
promoted == false
private_holdout_used == false
controller_family_ranking_claim_made == false
support_policy_ranking_claim_made == false
winner_selected == false
paper_level_claim_made == false
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
scenario_redesign_executed_claim_made == false
reset_valid_scenario_pack_claim_made == false
```

If any reset fails, M2353 must fail closed and route to result/failure audit. It
must not repair packs and rerun inside the same milestone.

## Failure Taxonomy

M2353 should classify failures as:

```text
manifest_load_failure
config_pack_schema_failure
metadata_caveat_join_failure
env_config_rebuild_failure
human_view_contract_violation
reset_sampling_failure
observation_contract_failure
guardrail_violation
```

Reset failure is scenario/task-quality evidence, not controller-family
evidence.

## Claim Boundary

If M2353 passes, it may claim only:

```text
the five M2350 candidate config packs are reset-valid under the current
simulator and strict human-view observation contract.
```

It still cannot claim:

```text
scenario redesign executed;
rollout success;
measured execution success;
support-policy ranking;
controller-family ranking;
winner selection;
paper-level benchmark evidence;
finite-window vs GRU result;
level3 self-identification evidence.
```

## Next

Next milestone:

```text
m2353-paper-route-current-sim-dual-axis-candidate-pack-reset-validation-implementation
```

M2353 may implement and run the frozen reset-only command. Interpretation must
be deferred to M2354 result audit.
