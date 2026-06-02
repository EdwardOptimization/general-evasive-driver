# M2398 Paper-Route Current-Sim Dual-Axis Effective Candidate Measured Validation Result Audit

- status: completed
- decision: `effective_candidate_measured_validation_complete_offtrack_dominated_route_to_outcome_localization`
- manifest: `experiments/manifests/m2398-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-result-audit.json`
- parent implementation: `docs/m2397-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-implementation.md`
- parent summary: `runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/summary.json`
- rerun/new rollout in M2398: `false`
- repair execution/training/replay/PPO: `false`
- support-policy/controller-family/effective-candidate ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2398 accepts M2397 as a complete measured artifact.

Accepted completeness evidence:

```text
result_class: current_sim_dual_axis_effective_candidate_measured_validation_pass
episode_count: 30735
target_episode_count: 30735
source_candidate_count: 54
candidate_scenario_reference_count: 2049
unique_pack_scenario_count: 350
selected_checkpoint_count: 15
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
actor_contract_violation_count: 0
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

No artifact-level failure was observed:

```text
metric_artifact: not observed
lineage_invalid: not observed
contract_violation: not observed
scenario_sampling_failure: not observed at artifact-construction level
```

The audit rejects the shortcut interpretation that a complete artifact means a
successful driver. M2397 is complete and clean, but its measured outcome is poor.

## Outcome Classification

Global M2397 outcome:

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
```

This is a driver-outcome blocker, not a metric or lineage blocker.

M2398 classifies the observed result as:

```text
artifact_status: accepted_complete
outcome_quality: offtrack_dominated_failure
paper_route_status: blocked
current_sim_verdict: not_made
ranking_status: not_admissible
```

## Diagnostic Slices

Profile aggregates are diagnostic-only. They suggest that `L3_online_gru` had
higher success than the finite-window/current-response profiles on this panel,
but M2398 does not admit a finite-window-vs-GRU conclusion because this is not a
controlled verdict protocol.

```text
L0_current_masked success/offtrack/collision: 0.027005043110460387 / 0.8884008459411095 / 0.0662111599154059
L1_one_step success/offtrack/collision: 0.026842362127867253 / 0.9105254595737758 / 0.05856515373352855
L2_window_25 success/offtrack/collision: 0.026842362127867253 / 0.838295103302424 / 0.12770457133561086
L2_window_50 success/offtrack/collision: 0.027005043110460387 / 0.8366682934764926 / 0.12949406214413536
L3_online_gru success/offtrack/collision: 0.09500569383439075 / 0.7390597039206117 / 0.1259150805270864
```

Role-family aggregates show the next localization target:

```text
R0_stable_avoidable success/offtrack/collision: 0.058694158075601376 / 0.9352577319587629 / 0.000549828178694158
R1_aeb_infeasible_stable_aes success/offtrack/collision: 0.33090909090909093 / 0.6638383838383838 / 0.0052525252525252525
R2_handling_limit_drift_capable_avoidance success/offtrack/collision: 0.0 / 0.8337662337662337 / 0.1479076479076479
R3_recovery_after_limit success/offtrack/collision: 0.0 / 0.8493984430290162 / 0.13319179051663127
R4_unavoidable_mitigation success/offtrack/collision: 0.0 / 0.3958974358974359 / 0.598974358974359
R5_hidden_dynamics_robustness success/offtrack/collision: 0.0 / 0.8786367414796342 / 0.09226932668329177
```

The high offtrack rate in R0/R1/R2/R3/R5 and the collision-dominated R4
semantics should be localized before any repair, training, or scenario-redesign
claim.

M2398 does not compare M2397 directly against M2362 as a regression because the
denominators differ. The stable interpretation is narrower: both panels are
offtrack-dominated, and M2397 confirms the effective-candidate panel did not
solve the offtrack outcome blocker.

## Failure Taxonomy

Observed:

```text
driver_outcome_failure: offtrack_dominated_failure
task_quality_blocker: effective candidates do not yet produce acceptable closed-loop success
collision_guardrail_signal: R4_unavoidable_mitigation is collision-dominated
```

Not observed:

```text
metric_artifact
lineage_invalid
contract_violation
scenario_sampling_failure at artifact-construction level
training_instability
```

Risk to manage next:

```text
diagnostic aggregate overfitting
profile/candidate ranking from non-ranking rows
repairing offtrack while worsening collision guardrails or R4 mitigation semantics
continuing artifact-only loops without a new localization artifact
```

## Claim Boundary

Supported:

```text
M2397 is a complete 30735-episode measured-validation artifact with clean
lineage and guardrails.

M2397 outcome is offtrack-dominated and requires outcome localization before
repair, training, ranking, or paper-route conclusions.
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

## Route Decision

Decision:

```text
effective_candidate_measured_validation_complete_offtrack_dominated_route_to_outcome_localization
```

Next milestone:

```text
m2399-paper-route-current-sim-dual-axis-effective-candidate-measured-outcome-localization-implementation
```

M2399 should be an artifact-only localization implementation over M2397
`episode_rows.csv` and aggregates. It should produce slice rows that separate
offtrack targets, collision guardrails, R4 mitigation semantics, and
diagnostic-only aggregates. It must not rerun rollout, execute repair, train,
rank candidates/profiles, select a winner, or make paper/self-ID/current-sim
verdict claims.
