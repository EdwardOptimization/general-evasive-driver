# M2253 Paper-Route Current-Sim Offtrack/Recovery/Corridor Selected-Checkpoint Outcome Localization Implementation

- status: completed
- decision: `current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2253-paper-route-current-sim-offtrack-recovery-corridor-selected-checkpoint-outcome-localization-implementation.json`
- result artifact: `runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/summary.json`
- selected checkpoint source: `runs/m2250_paper_route_current_sim_offtrack_recovery_corridor_training_execution/selected_checkpoint_rows.csv`

## Execution Result

M2253 completed the fixed selected-checkpoint localization panel:

```text
result_class: current_sim_selected_checkpoint_outcome_localization_pass
selected_checkpoint_count: 15
episode_row_count: 480
expected_episode_row_count: 480
profile_seed_group_count: 15
profile_seed_groups_complete: true
missing_input_count: 0
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

The primary repair route emitted by the runner remains:

```text
offtrack_recovery_reward_and_corridor_repair_design
```

## Global Outcome

M2253 global outcome over `480` repaired selected-checkpoint episodes:

| outcome | count | rate |
| --- | ---: | ---: |
| success | `269` | `0.56042` |
| offtrack | `118` | `0.24583` |
| collision | `93` | `0.19375` |
| max-step noncompletion | `0` | `0.0` |

Global dominant failure mode:

```text
offtrack_dominated_failure
```

The important comparison against M2244:

| metric | M2244 selected panel | M2253 repaired selected panel | delta |
| --- | ---: | ---: | ---: |
| success count | `277/480` | `269/480` | `-8` |
| offtrack count | `110/480` | `118/480` | `+8` |
| collision count | `93/480` | `93/480` | `0` |
| max-step noncompletion | `0/480` | `0/480` | `0` |
| mean return | `49.83740` | `64.21352` | `+14.37612` |

Return improved, but the actual outcome distribution did not improve. Offtrack
got worse and collision stayed unchanged.

## Profile Outcomes

| profile | success | offtrack | collision | dominant failure mode |
| --- | ---: | ---: | ---: | --- |
| L0_current_masked | `55/96` | `23/96` | `18/96` | `offtrack_dominated_failure` |
| L1_one_step | `57/96` | `27/96` | `12/96` | `offtrack_dominated_failure` |
| L2_window_25 | `56/96` | `22/96` | `18/96` | `offtrack_dominated_failure` |
| L2_window_50 | `56/96` | `22/96` | `18/96` | `offtrack_dominated_failure` |
| L3_online_gru | `45/96` | `24/96` | `27/96` | `collision_dominated_failure` |

Profile-seed rows retain local success-supported islands:

```text
L0_current_masked|222603
L1_one_step|222603
L2_window_25|222601
L2_window_50|222601
```

But the weak profile-seed rows remain dominated by offtrack, with
`L3_online_gru|222602` collision-dominated.

## Classification

Primary classification:

```text
return_improved_but_offtrack_repair_failed
```

Supported:

- M2253 is a complete and guardrail-clean outcome-localization artifact.
- M2250 reward repair improved scalar return.
- Scalar return improvement does not imply actual outcome repair.
- The repaired panel remains offtrack dominated globally.

Not supported:

- The reward extension repaired the offtrack blocker.
- The panel is comparison-ready.
- Another identical reward-extension training run is justified without audit.
- Any controller-family ranking, finite-window-vs-GRU verdict, paper-level
  result, or level3 self-identification claim.

## Artifact Note

The reusable localization runner still writes `run_state.task_id` using its
historical default task id. The M2253 summary, output directory, next blocker,
and all episode/aggregate artifacts are correct; the task-id metadata issue is
not an episode-semantics change. M2254 may decide whether to schedule a
default-preserving metadata cleanup, but it should not distract from the
outcome result.

## Route Decision

The execution command wrote the old result-audit next-blocker label, but the
research harness local-search guard escalates the follow-up to branch synthesis.

Route to:

```text
m2254-paper-route-current-sim-offtrack-recovery-corridor-branch-synthesis
```

The audit should decide between:

```text
stronger offtrack/recovery/corridor repair
collision/clearance guardrail repair for L3-specific regressions
branch synthesis because the bounded reward repair failed its outcome purpose
```

## Blocked Claims

Still blocked:

```text
controller-family ranking
winner selection
measured execution as comparison evidence
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
private holdout
another blind budget escalation
another identical offtrack reward-extension run before audit
```

## Next

Pre-register:

```text
m2254-paper-route-current-sim-offtrack-recovery-corridor-branch-synthesis
```
