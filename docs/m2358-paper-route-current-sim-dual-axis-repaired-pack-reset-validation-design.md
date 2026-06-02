# M2358 Paper-Route Current-Sim Dual-Axis Repaired Pack Reset Validation Design

- status: completed
- decision: `repaired_pack_reset_validation_design_admit_reset_only_implementation`
- manifest: `experiments/manifests/m2358-paper-route-current-sim-dual-axis-repaired-pack-reset-validation-design.json`
- parent audit: `docs/m2357-paper-route-current-sim-dual-axis-candidate-pack-sampling-repair-result-audit.md`
- repaired pack manifest: `runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repaired_config_pack_manifest.json`
- reset/rollout/policy action in M2358: `false`
- measured execution in M2358: `false`
- training/replay/PPO in M2358: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`
- reset-valid repaired pack claim made: `false`

## Design Goal

M2358 freezes the reset-only validation route for the five M2356 repaired
candidate packs. It does not run reset validation. M2359 may run reset
validation only if it preserves the repair metadata and follows the exact
workload below.

Target workload:

```text
config_pack_count: 5
scenario_specs_per_pack: 72
reset_attempt_count: 360
rollout_steps: 0
policy_actions: 0
expected_observation_dim: 72
```

## Inputs

M2359 should read:

```text
runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repaired_config_pack_manifest.json
runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repair_action_rows.csv
runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repaired_scenario_spec_patch_rows.csv
runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/effective_pack_summary_rows.csv
```

The repaired-pack validator should not read or overwrite the active scenario
config.

## M2359 Command

M2359 should implement and run:

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

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_dual_axis_repaired_pack_reset_validation.py
```

## Required Metadata Preservation

M2359 reset rows should include:

```text
pack_id
scenario_spec_id
scenario_index
eval_seed
sampling_repair_applied
sampling_repair_action
sampling_repair_class
sampling_repair_source_candidate_id
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
support_policy_ranking_claim_made
controller_family_ranking_claim_made
paper_level_claim_made
finite_window_vs_gru_conclusion_made
level3_self_id_claim_made
scenario_redesign_executed_claim_made
reset_valid_repaired_pack_claim_made
```

M2359 summary should preserve:

```text
baseline_env_config_fallback_count: 32
timing_related_repair_count: 27
hidden_only_repair_count: 3
lateral_hidden_repair_count: 2
effective_selection_counts:
  g_primary_pack: 4
  h_primary_pack: 12
  g_h_primary_pack: 16
  gh_minimal_pack: 14
metadata_only_patch_count: 37
```

## Expected Artifacts

M2359 must write:

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

## Pass Gates

M2359 passes only if:

```text
result_class == current_sim_dual_axis_repaired_pack_reset_validation_pass
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
baseline_env_config_fallback_count == 32
repair_action_rows_preserved == true
metadata_caveat_rows_preserved == true
metadata_only_patch_count == 37
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
support_policy_ranking_claim_made == false
controller_family_ranking_claim_made == false
winner_selected == false
paper_level_claim_made == false
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
scenario_redesign_executed_claim_made == false
reset_valid_repaired_pack_claim_made == false
```

If any reset fails, M2359 must fail closed and route to result/failure audit. It
must not repair and rerun inside the same milestone.

## Claim Boundary

If M2359 passes, it may claim only:

```text
the five M2356 repaired candidate config packs are reset-valid under the
current simulator and strict human-view observation contract.
```

It still cannot claim:

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

## Next

Next milestone:

```text
m2359-paper-route-current-sim-dual-axis-repaired-pack-reset-validation-implementation
```

M2359 may implement and run the frozen reset-only command. Interpretation must
be deferred to M2360 result audit.
