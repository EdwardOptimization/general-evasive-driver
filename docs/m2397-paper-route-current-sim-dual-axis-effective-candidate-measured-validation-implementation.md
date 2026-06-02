# M2397 Paper-Route Current-Sim Dual-Axis Effective Candidate Measured Validation Implementation

- status: completed
- result class: `current_sim_dual_axis_effective_candidate_measured_validation_pass`
- manifest: `experiments/manifests/m2397-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_effective_candidate_measured_validation.py`
- focused tests: `3 passed`
- summary: `runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/summary.json`
- episode rows: `runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/episode_rows.csv`
- reset-validation source: `runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/summary.json`
- repair execution/training/replay/PPO: `false`
- support-policy/controller-family/effective-candidate ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Implementation Result

M2397 implements and runs the M2396 measured-validation protocol over the
reset-ready effective candidate artifacts from M2391/M2394.

The run completed the full fixed denominator:

```text
source_candidate_count: 54
candidate_scenario_reference_count: 2049
unique_pack_scenario_count: 350
selected_checkpoint_count: 15
target_episode_count: 30735
episode_count: 30735
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
actor_contract_violation_count: 0
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

The measured denominator remains:

```text
candidate_id + pack_id + scenario_spec_id + selected_checkpoint
```

The 350 unique pack/scenario targets remain reset-readiness evidence only; they
are not the measured denominator.

## Outcome Snapshot

The artifact pass is a data-completeness and guardrail pass, not a driver
performance pass.

Global measured outcome:

```text
success_count: 1246
success_rate: 0.04054010086220921
collision_count: 3122
collision_rate: 0.10157800553115341
offtrack_count: 25897
offtrack_rate: 0.8425898812428827
max_step_noncompletion_count: 266
max_step_noncompletion_rate: 0.008654628273954775
other_failure_count: 204
other_failure_rate: 0.006637384089799902
dominant_failure_mode: offtrack_dominated_failure
mean_return: 16.793719564152678
mean_steps: 108.2529363917358
mean_min_clearance_margin: 8.497377506922128
min_min_clearance_margin: -0.34421275286318664
mean_max_off_track_overshoot: 0.05994599168635331
mean_high_sideslip_fraction: 0.11088096138274543
mean_action_rate: 0.005436075364744188
```

Outcome counts:

```text
collision_failure: 3122
max_steps_noncompletion: 266
off_track_noncollision_noncompletion: 25897
speed_too_low_noncollision_noncompletion: 290
success_obstacle_pass: 1160
```

Termination reason counts:

```text
obstacle_collision: 3058
off_track: 25961
speed_too_low: 290
blank/other: 1426
```

This is a strong signal that the current effective-candidate panel is still
offtrack-dominated. M2397 therefore supports measured data availability and
lineage completeness, not current-sim driver readiness.

## Diagnostic Aggregates

Profile aggregates remain diagnostic-only and non-ranking:

```text
L0_current_masked success_rate/offtrack_rate/collision_rate: 0.027005043110460387 / 0.8884008459411095 / 0.0662111599154059
L1_one_step success_rate/offtrack_rate/collision_rate: 0.026842362127867253 / 0.9105254595737758 / 0.05856515373352855
L2_window_25 success_rate/offtrack_rate/collision_rate: 0.026842362127867253 / 0.838295103302424 / 0.12770457133561086
L2_window_50 success_rate/offtrack_rate/collision_rate: 0.027005043110460387 / 0.8366682934764926 / 0.12949406214413536
L3_online_gru success_rate/offtrack_rate/collision_rate: 0.09500569383439075 / 0.7390597039206117 / 0.1259150805270864
```

Role-family aggregates show that the panel is not uniformly hard in the same
way:

```text
R0_stable_avoidable success_rate/offtrack_rate/collision_rate: 0.058694158075601376 / 0.9352577319587629 / 0.000549828178694158
R1_aeb_infeasible_stable_aes success_rate/offtrack_rate/collision_rate: 0.33090909090909093 / 0.6638383838383838 / 0.0052525252525252525
R2_handling_limit_drift_capable_avoidance success_rate/offtrack_rate/collision_rate: 0.0 / 0.8337662337662337 / 0.1479076479076479
R3_recovery_after_limit success_rate/offtrack_rate/collision_rate: 0.0 / 0.8493984430290162 / 0.13319179051663127
R4_unavoidable_mitigation success_rate/offtrack_rate/collision_rate: 0.0 / 0.3958974358974359 / 0.598974358974359
R5_hidden_dynamics_robustness success_rate/offtrack_rate/collision_rate: 0.0 / 0.8786367414796342 / 0.09226932668329177
```

These aggregates are useful for M2398 audit and possible localization, but they
are not admissible rankings or winners.

## Claim Boundary

Supported:

```text
M2397 produced a complete 30735-episode measured-validation artifact over the
M2391/M2394 reset-ready effective candidate panel, with preserved
candidate/pack/scenario/checkpoint lineage and no contract, metadata, metric,
or guardrail violations.
```

Blocked:

```text
effective-candidate ranking
controller-family ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
scenario redesign executed
training repair success
current-sim verdict
```

The reason is that M2397 is the first measured data pass for this denominator.
Its aggregate outcome is offtrack-dominated and must be audited before any
route decision.

## Route Decision

Decision:

```text
effective_candidate_measured_validation_pass_route_to_result_audit
```

Next milestone:

```text
m2398-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-result-audit
```

M2398 should audit M2397 as a complete but offtrack-dominated measured panel. It
should classify whether the next bounded route is outcome localization,
scenario-quality reassessment, repair-plan revision, branch synthesis, or stop.
It must not rank candidates, select a winner, or make paper/self-ID/current-sim
verdict claims.
