# M1939 Executable V2 Task-Quality Measured Execution Result Audit

- status: completed
- decision: `task_quality_measured_execution_audit_blocks_ranking_routes_to_branch_synthesis`
- branch: `paper_route_task_quality_reset_execution`
- audited summary: `runs/m1938_executable_v2_task_quality_measured_execution/summary.json`
- reset/rollout/measured execution in M1939: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Completeness Audit

M1938 is complete as a public diagnostic measured execution artifact.

Pass-gate fields:

```text
result_class: task_quality_measured_execution_pass
episode_count: 960
failure_count: 0
spec_count: 80
profile_count: 12
tier_count: 5
role_count: 4
surface_count: 2
metric_completeness_failure_count: 0
all_selected_metrics_finite: true
guardrail_violation_count: 0
```

Guardrails:

```text
environment_rollout_started: true
policy_action_executed: true
measured_rollout_started: true
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
profile_specific_tuning: false
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Raw Outcome Structure

Overall outcome counts:

```text
success_obstacle_pass: 40 / 960 = 4.17%
collision_failure: 105 / 960 = 10.94%
off_track_noncollision_noncompletion: 815 / 960 = 84.90%
```

Profile-level success:

```text
L1_one_step: 12 / 80 = 15.00%
L0_current_masked: 10 / 80 = 12.50%
L3_online_gru: 9 / 80 = 11.25%
L3_reset_control_corrected: 9 / 80 = 11.25%
all L2 finite-window/current-tiled profiles: 0 / 80 = 0.00% each
```

Role-level success:

```text
stable_aeb: 18 / 240 = 7.50%
stable_aes_only: 8 / 240 = 3.33%
drift_required_recovery: 8 / 240 = 3.33%
unavoidable_mitigation: 6 / 240 = 2.50%
```

Tier-level success:

```text
tier_a_positive_support_sanity: 1 / 192 = 0.52%
tier_b_feasible_emergency: 10 / 192 = 5.21%
tier_c_boundary_near_miss: 14 / 192 = 7.29%
tier_d_handling_limit_drift_required: 8 / 192 = 4.17%
tier_e_mitigation_only: 7 / 192 = 3.65%
```

The panel is not zero-success, which is better than the earlier fixed-source
repair-axis branch. But outcome support is still weak and dominated by
off-track noncollision noncompletion. Direct controller ranking would be
premature because the main signal is still scenario/controller interaction
failure, not a robust ranking surface.

## Supported Claims

M1939 supports:

- the M1938 measured execution completed cleanly;
- the redesigned task-quality panel has nonzero success support;
- the run preserved all target counts and metadata dimensions;
- measured rollout infrastructure can now generate complete public diagnostic
  artifacts over the reset-valid M1928 panel;
- direct ranking remains blocked by low support and off-track-dominated
  outcomes.

## Unsupported Claims

Still unsupported:

- controller-family ranking;
- finite-window vs GRU conclusion;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification.

Notably, the fact that `L1_one_step`, `L0_current_masked`, and `L3` have nonzero
success while all `L2` profiles have zero success is diagnostic. It should be
localized before being treated as a controller-family conclusion.

## Failure Taxonomy

M1939 classifies the current blocker as:

```text
outcome_support_low_offtrack_dominated
```

It is not:

```text
reset_sampling_failure
measured_runner_failure
metric_artifact
contract_violation
private_holdout_leak
controller_ranking_evidence
level3_self_id_evidence
```

## Next Route

This branch has reached the 10-milestone synthesis cadence:

```text
M1930-M1939
```

Therefore the next task should be branch synthesis, not another immediate
local repair or rollout.

Next milestone:

```text
m1940-executable-v2-task-quality-reset-execution-branch-synthesis
```

M1940 should decide whether the next branch should be:

- no-rerun outcome localization over M1938 artifacts;
- task-quality repair of off-track dominance;
- measured comparison design with strict non-ranking claim boundary;
- or a pivot back to scenario design.

Until synthesis completes, controller ranking, paper-level claims, and level3
self-ID claims remain blocked.
