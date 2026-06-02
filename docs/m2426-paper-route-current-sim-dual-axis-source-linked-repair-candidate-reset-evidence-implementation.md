# M2426 Paper-Route Current-Sim Dual-Axis Source-Linked Repair-Candidate Reset Evidence Implementation

- status: completed
- result_class: `current_sim_dual_axis_source_linked_repair_candidate_reset_evidence_fail_closed`
- manifest: `experiments/manifests/m2426-paper-route-current-sim-dual-axis-source-linked-repair-candidate-reset-evidence-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_source_linked_repair_candidate_reset_evidence.py`
- focused tests: `3 passed`
- summary: `runs/m2426_paper_route_current_sim_dual_axis_source_linked_repair_candidate_reset_evidence/summary.json`
- environment step / policy action / measured rollout: `0 / false / false`
- repair / training / replay / PPO: `false / false / false / false`
- ranking / winner / current-sim verdict: `false / false / false`

## Result

M2426 materialized and ran the reset-only source-linked repair-candidate panel.
The implementation is cleanly fail-closed: reset and actor-contract validation
passed for every concrete target it could materialize, but one M2422 candidate
family has no M2391 effective-candidate source match.

```text
candidate_overlay_load_count: 4
candidate_family_count: 4
matched_family_count: 3
family_without_match_count: 1
fail_closed_unmatched_source_key_result_recorded: true
source_effective_candidate_count: 54
matched_effective_candidate_count: 54
source_linked_scenario_reference_count: 2049
unique_reset_target_count: 350
unmatched_source_key_count: 5
static_validation_failure_count: 0
environment_reset_attempt_count: 350
environment_reset_success_count: 350
environment_reset_failure_count: 0
environment_step_count: 0
policy_action_executed: false
guardrail_violation_count: 0
failure_types_observed: family_source_link_failure
```

## Family Coverage

```text
c01_source_linked_geometry_timing_containment:
  matched effective candidates: 3
  scenario refs: 388
  unique reset targets: 290
  unmatched source keys: 2
  reset pass: true

c02_source_linked_hidden_dynamics_response_containment:
  matched effective candidates: 24
  scenario refs: 593
  unique reset targets: 280
  unmatched source keys: 2
  reset pass: true

c03_source_linked_role_conditioned_containment:
  matched effective candidates: 27
  scenario refs: 1068
  unique reset targets: 300
  unmatched source keys: 0
  reset pass: true

c04_source_linked_outcome_failure_surface_containment:
  matched effective candidates: 0
  scenario refs: 0
  unique reset targets: 0
  unmatched source keys: 1
  reset pass: false
```

The unmatched keys are:

```text
c01: episode_rows:obstacle_lateral_offset_bucket:right_offset
c01: episode_rows:obstacle_longitudinal_timing_bucket:mid
c02: episode_rows:hidden_dynamics_bucket:same_scene_balanced_panel
c02: episode_rows:role_family+hidden_dynamics_bucket:R5_hidden_dynamics_robustness|same_scene_balanced_panel
c04: episode_rows:outcome_bucket:off_track_noncollision_noncompletion
```

## Boundary Checks

Reset-only boundary:

```text
environment_reset_started: true
environment_step_count: 0
policy_action_executed: false
measured_rollout_started: false
repair_execution_started: false
training_started: false
replay_started: false
ppo_used: false
```

Contract and claim boundary:

```text
static_validation_failure_count: 0
actor_input_contract_changed: false
hidden_oracle_feature_injection: false
active_config_overwrite_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
paper_level_claim_made: false
finite_window_vs_gru_conclusion_made: false
level3_self_id_claim_made: false
scenario_redesign_executed_claim_made: false
training_repair_success_claim_made: false
current_sim_verdict_claim_made: false
```

## Interpretation

Supported:

```text
M2426 created a concrete reset-only panel for the matched executable subset of
the M2422 source-linked repair-candidate overlays.

The matched subset is reset-clean: 350/350 unique env configs reset, static
actor-contract validation passes, and no environment step or policy action is
executed.

The implementation correctly preserves fail-closed source coverage diagnostics.
```

Blocked:

```text
M2426 does not admit measured validation over all four candidate families.

c04_source_linked_outcome_failure_surface_containment cannot be measured through
the M2391 effective-candidate panel because its outcome_bucket source key has no
matched executable scenario spec.

M2426 does not prove scenario repair, driver improvement, controller-family
ranking, finite-window-vs-GRU result, self-identification, paper-level evidence,
or current-sim verdict.
```

## Next

Follow-up manifest:

```text
experiments/manifests/m2427-paper-route-current-sim-dual-axis-source-linked-repair-candidate-reset-evidence-result-audit.json
```

M2427 must audit the fail-closed result before any measured-validation design.
The audit should choose between:

```text
1. route to source-coverage repair for c04/outcome_bucket before measured validation;
2. route to bounded measured-validation design for the matched 3-family subset
   with an explicit c04 exclusion caveat;
3. pivot to scenario-quality reassessment if outcome-failure-surface coverage is
   required for the paper route;
4. stop/synthesize if another artifact-only step would not produce new evidence.
```
