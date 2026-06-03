# M2466 Paper-Route Current-Sim Dual-Axis Scenario-Quality R1 Reset Sampling Diagnostic Panel

- status: completed
- result_class: `scenario_quality_r1_reset_sampling_diagnostic_panel_complete`
- manifest: `experiments/manifests/m2466-paper-route-current-sim-dual-axis-scenario-quality-r1-reset-sampling-diagnostic-panel.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_scenario_quality_r1_reset_sampling_diagnostic_panel.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_scenario_quality_r1_reset_sampling_diagnostic_panel.py`
- summary: `runs/m2466_paper_route_current_sim_dual_axis_scenario_quality_r1_reset_sampling_diagnostic_panel/summary.json`
- reset/rollout/policy action/scenario-redesign execution/repair/training/replay/PPO in M2466: `reset_only`
- ranking/winner selection in M2466: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign-executed/training-repair/current-sim verdict claims: `false`

## Source Admission

M2466 admitted the M2464 R1 stable-AES reset evidence:

```text
source_admission_failure_count: 0
r1_source_target_count: 3
source_overlay_hash_count: 1
source_unique_effective_config_count: 1
target_overlay_family: R1_aeb_infeasible_stable_aes
source_overlay_hash: 0688da6aec7f7314b7a46bbeb62af90313abddffea344d5d1ad1363f5acd678b
source_reset_target_ids: m2464_reset_target_004, m2464_reset_target_005, m2464_reset_target_006
```

The admitted parent result remains reset-only evidence from M2464: three R1
targets shared one effective config and overlay hash, with one reset success and
two `scenario_sampling_failure` rows.

## Diagnostic Result

M2466 ran five diagnostic-only variants across 24 reset seeds each:

```text
variant_count: 5
diagnostic_attempt_count: 120
reset_success_count: 20
reset_failure_count: 100
guardrail_violation_count: 0
environment_step_count: 0
policy_action_executed: false
environment_rollout_started: false
repair_execution_started: false
training_started: false
ranking_admissible_count: 0
winner_selected_count: 0
```

Variant reset outcomes:

```text
baseline_r1_original: 5/24 success, 19/24 scenario_sampling_failure
nominal_hidden_dynamics: 0/24 success, 24/24 scenario_sampling_failure
threshold_relaxed: 5/24 success, 19/24 scenario_sampling_failure
geometry_wider_same_threshold: 5/24 success, 19/24 scenario_sampling_failure
threshold_and_geometry_relaxed: 5/24 success, 19/24 scenario_sampling_failure
```

The classification is:

```text
diagnostic_classification: seed_fragility
failure_types_observed: scenario_sampling_failure, seed_fragility
```

The diagnostic did not find support for hidden-dynamics randomization fragility,
threshold strictness, geometry-range fragility, or a coupled threshold/geometry
effect under the tested variants. Threshold relaxation, geometry widening, and
their combination matched the baseline `5/24` reset success rate. Collapsing
hidden dynamics to nominal deterministic ranges reduced success to `0/24`.

## Interpretation Boundary

Supported claim:

```text
The M2464 R1 stable-AES blocker is seed-fragile reset sampling under the current
R1 effective config family: reset succeeds for some seeds and fails for most
seeds in the 24-seed panel.
```

Rejected claims:

```text
driver performance improvement
measured actual-success improvement
scenario redesign executed
repair/training success
support-policy/controller/checkpoint/scenario ranking
winner selection
paper-level result
finite-window vs GRU conclusion
level3 self-identification
current-sim verdict
```

All diagnostic variants are run-dir-only artifacts. They are not repaired
overlays, repair candidates, rankings, winners, promoted configs, or evidence of
driver capability.

## Decision

M2466 routes to:

```text
m2467-paper-route-current-sim-dual-axis-scenario-quality-r1-reset-sampling-diagnostic-panel-result-audit
```

M2467 must audit the seed-fragility result before any sampler repair, overlay
repair, reset-validation retry, measured rollout, training, ranking, winner
selection, or verdict route. Because the local-search guard has now seen the
same scenario-sampling blocker across M2464, M2465, and M2466, M2467 must either
select a bounded evidence-expanding route or synthesize/pivot instead of
continuing another narrow scenario-sampling process milestone.
