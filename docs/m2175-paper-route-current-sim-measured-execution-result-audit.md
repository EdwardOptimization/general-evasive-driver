# M2175 Paper-Route Current-Sim Measured Execution Result Audit

- status: completed
- decision: `current_sim_measured_execution_audit_route_to_training_seed_repeat_design`
- manifest: `experiments/manifests/m2175-paper-route-current-sim-measured-execution-result-audit.json`
- audited summary: `runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution/summary.json`
- rerun in M2175: `false`
- training/replay/PPO in M2175: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Completeness Audit

M2174 is a clean measured-execution run:

```text
episode_count = 320
failure_count = 0
spec_count = 40
profile_count = 8
metadata_missing_count = 0
metric_completeness_failure_count = 0
task_family_quota_pass = true
profile_quota_pass = true
history_representation_quota_pass = true
guardrail_violation_count = 0
```

This supports an execution-completeness claim:

```text
The current-sim 320-cell panel can be executed end to end with the M2171
materialized checkpoints and M2168 runner adapter.
```

## Outcome Support Audit

Raw outcome counts:

```text
success_obstacle_pass = 63 / 320
collision_failure = 20 / 320
off_track_noncollision_noncompletion = 237 / 320
```

The global success rate is `0.196875`. The run is therefore not yet a
paper-grade comparison result. It is offtrack-dominated and uses one training
seed per trainable profile.

Descriptive profile success rates from the M2174 aggregate:

```text
L0_current_masked = 0.125
L1_one_step = 0.175
L2_window_13 = 0.000
L2_window_25 = 0.850
L2_window_50 = 0.350
L2_window_100 = 0.075
L3_online_gru = 0.000
L3_reset_control = 0.000
```

These values are not a ranking. They show that the benchmark and runner can
produce nontrivial profile-dependent behavior, but the evidence is still
seed-fragile because each trainable profile has only one 1024-step smoke
checkpoint.

Task-family success rates:

```text
T1_reactive_emergency_avoidance = 0.296875
T2_delayed_actuator_response = 0.28125
T3_diagnostic_warmup_obstacle_reveal = 0.21875
T4_same_current_different_older_history = 0.125
T5_terminal_boundary_near_constraint = 0.0625
```

T4/T5 remain difficult. This is useful diagnostic signal, but not enough to
choose a controller family.

## Failure Taxonomy

The execution layer passed. The active evidence limitation is:

```text
seed_fragility / comparison_underpowered:
  one training seed per trainable profile;
  smoke-scale total_steps = 1024;
  no repeat training seeds;
  no confidence intervals or per-seed variance.
```

Secondary limitation:

```text
outcome_support_low_offtrack_dominated:
  237 / 320 episodes end as off_track_noncollision_noncompletion.
```

No evidence of:

```text
contract_violation
metric_artifact
metadata loss
measured runner failure
profile-specific tuning
private holdout contamination
```

## Decision

Decision:

```text
current_sim_measured_execution_audit_route_to_training_seed_repeat_design
```

Do not proceed to controller ranking, finite-window vs GRU verdict, or
paper-level comparison yet.

The next step should design a controlled training-seed repeat:

```text
same 40 specs;
same 8 profile definitions;
same measured runner;
same evaluation seed policy;
multiple frozen training seeds per trainable profile;
L3_reset_control remains an alias to the same-seed L3_online_gru checkpoint;
no profile-specific tuning;
no ranking until repeat results are audited.
```

The purpose is to answer whether the visible profile differences in M2174 are
stable or just a smoke-training seed artifact.
