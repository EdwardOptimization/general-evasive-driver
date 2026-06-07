# M3019 Engineering Controller Route A Post-Residual-Stop New Source Failure Localization Materialization Result Audit

## Metadata

- status: completed
- decision: `accept_m3018_claim_safe_localization_route_to_m3020_result_synthesis`
- manifest: `experiments/manifests/m3019-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-materialization-result-audit.json`
- parent preflight: `runs/m3018_engineering_controller_route_a_post_residual_stop_new_source_failure_localization_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m3020-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-result-synthesis.json`
- next: `m3020-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-result-synthesis`

M3019 is a result audit. It does not reset, step, rollout, replay, validate,
train, rank, promote, mutate checkpoints, tune profiles, select a repair
target, or claim performance.

## Audit Result

M3019 accepts M3018 as complete and claim-safe localization materialization:

```text
M3018 status_pass: true
M3018 gate_matrix_pass: true
M3018 required_artifacts_present: true
source specs: 16/16
unique M3006 task_source ids: 16/16
scheduled workload rows: 32/32
episode rows localized: 32/32
failure rows preserved: 0
profile/source aggregate rows: 32
profile bindings: 2
actor contract: observation 72, action 3
```

M3018 preserved the fixed M3015 denominator and registered the M3019 audit
manifest. All M3018 gate rows passed, including denominator, actor contract,
claim-boundary, no-execution, and no-overclaim checks.

## Localization Accounting

The accepted localization surface remains diagnostic-only:

```text
success rows: 3
collision rows: 5
off_track terminations: 23
obstacle_collision terminations: 4
speed_too_low terminations: 2
blank termination rows: 3
failure localization rows: 32
```

The localized failure families are:

```text
collision_clearance_failure: 5
offtrack_high_severity_recovery_failure: 5
offtrack_recovery_failure: 17
speed_floor_context: 2
success_context: 3
```

By profile, the candidate produced no success rows:

```text
route_a_candidate_m2655_mitigation_preserving: 12 off_track, 2 speed_too_low, 2 collision, 0 success
route_a_parent_l3_online_gru: 10 off_track, 3 collision, 3 success
```

Thirteen of the sixteen task_source ids remain non-success for both profiles.
Three task_source ids have parent success with candidate failure. This is enough
to show that the M3015/M3018 diagnostic surface is negative and broad, but not
enough to choose a repair target, rank profiles, or claim a verdict.

## Claim Boundary

M3019 verifies the M3018 claim boundary:

```text
environment_reset_run: false
environment_step_run: false
policy_action_run: false
policy_rollout_run: false
training_run: false
replay_run: false
ppo_run: false
ranking_run: false
winner_selected: false
checkpoint_mutated: false
checkpoint_promoted: false
profile_specific_tuning: false
repair_target_selected: false
validation_result_claim_made: false
driver_performance_claim_made: false
repair_success_claim_made: false
paper_claim_made: false
current_sim_verdict_claim_made: false
high_fidelity_validation_claim_made: false
finite_window_vs_gru_claim_made: false
full_ideal_driver_completion_claim_made: false
level3_self_id_claim_made: false
hidden_oracle_actor_input_detected: false
future_target_actor_input_required: false
source_labels_actor_visible: false
route_labels_actor_visible: false
outcome_labels_actor_visible: false
success_progress_labels_actor_visible: false
verdict_labels_actor_visible: false
ttc_actor_input_required: false
```

M3019 therefore rejects direct interpretation of M3018 as validation,
repair-success, driver-performance, current-sim verdict, paper,
high-fidelity, finite-window-vs-GRU, full-driver, ranking, promotion, or
self-identification evidence.

## Decision

M3019 accepts M3018 as complete and claim-safe, but rejects direct repair,
training, ranking, profile tuning, or promotion from the localization rows.
The failure distribution is broad and mixed: offtrack dominates, collision and
speed-floor failures remain, and most sources fail under both profiles.

The next route is M3020 result synthesis. M3020 must synthesize the audited
localization evidence and choose exactly one bounded continuation, pivot, or
stop state before any repair target, training, validation, performance, paper,
high-fidelity, finite-window-vs-GRU, full-driver, ranking, promotion, or self-ID
claim.
