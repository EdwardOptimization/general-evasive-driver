# M2205 Paper-Route Current-Sim Offtrack-Support Measured-Execution Result Audit

- status: completed
- decision: `current_sim_offtrack_support_measured_execution_audit_route_to_repeat_metadata_activation_repair_design`
- manifest: `experiments/manifests/m2205-paper-route-current-sim-offtrack-support-measured-execution-result-audit.json`
- audited summary: `runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/summary.json`
- validation failures: `runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/validation_failure_rows.csv`
- metadata missing rows: `runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/metadata_missing_rows.csv`
- follow-up manifest: `experiments/manifests/m2206-paper-route-current-sim-measured-runner-repeat-metadata-activation-repair-design.json`
- measured execution in M2205: `false`
- policy action executed in M2205: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2204 failed closed before rollout:

```text
result_class: current_sim_controlled_comparison_measured_execution_incomplete_or_fail
episode_count: 0
target_episode_count: 2304
metadata_missing_count: 2304
metric_completeness_failure_count: 0
guardrail_violation_count: 0
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
```

All workload rows have the same missing repeat metadata fields:

```text
training_repeat_id: 2304 missing
training_seed_group: 2304 missing
profile_training_seed: 2304 missing
profile_checkpoint_source_profile: 2304 missing
base_workload_id: 2304 missing
```

The measured runner code has the intended M2181 compatibility rule:

```text
Non-repeat workloads remain valid without repeat fields.

If any repeat metadata value is non-empty for a workload row, all repeat
metadata fields must be non-empty before rollout may start.
```

The live issue is that `checkpoint_materialization_mode` is included in the
repeat metadata tuple and M2200 legitimately writes it for every non-repeat
workload row:

```text
checkpoint_materialization_mode: train_frozen_profile_config
checkpoint_materialization_mode: alias_same_weights_reset_hidden_control
```

That single non-empty field activates the repeat completeness check even though
the workload is not a repeat workload.

## Classification

Failure type:

```text
metric_artifact
```

More specific classification:

```text
measured_runner_repeat_metadata_activation_overreach
```

This is not driver-performance evidence. It is a pre-rollout schema-validation
artifact caused by treating a mixed-purpose checkpoint provenance field as a
repeat-mode activation signal.

## Rejected Repairs

Do not fix this by writing fake repeat IDs into the workload:

```text
training_repeat_id = repeat_not_applicable
training_seed_group = not_applicable
profile_training_seed = not_applicable
profile_checkpoint_source_profile = not_applicable
base_workload_id = workload_id
```

That would make non-repeat workloads look like repeat workloads and could
pollute repeat aggregation.

Do not remove `checkpoint_materialization_mode` from the workload:

```text
checkpoint_materialization_mode
```

It is useful checkpoint provenance and should remain available in episode rows.

## Repair Route

M2206 should design a measured-runner compatibility repair:

```text
repeat mode is activated by repeat identity fields:
  training_repeat_id
  training_seed_group
  profile_training_seed
  profile_checkpoint_source_profile
  base_workload_id

checkpoint_materialization_mode alone does not activate repeat mode.

If any repeat identity field is non-empty, all repeat identity fields plus
checkpoint_materialization_mode must be non-empty.

If no repeat identity field is non-empty, checkpoint_materialization_mode may
still be preserved as normal checkpoint provenance.
```

Required focused tests:

```text
1. non-repeat workload with checkpoint_materialization_mode passes fake rollout;
2. repeat workload with all repeat identity fields passes and writes repeat aggregate;
3. partial repeat identity field still fails closed before rollout;
4. missing checkpoint path still fails closed.
```

## Claim Boundary

Supported by M2205:

```text
M2204 is a pre-rollout measured-runner metadata validation artifact, not a
driver-performance result.
```

Still unsupported:

```text
measured rollout success;
controller-family ranking;
policy performance comparison;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next Step

M2206 must design the repeat-metadata activation repair. No rerun is allowed
until that design is implemented, tested, and audited.
