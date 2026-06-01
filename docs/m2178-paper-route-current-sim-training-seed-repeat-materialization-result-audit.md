# M2178 Paper-Route Current-Sim Training-Seed Repeat Materialization Result Audit

- status: completed
- decision: `current_sim_repeat_materialization_audit_route_to_metadata_preserving_runner_design`
- manifest: `experiments/manifests/m2178-paper-route-current-sim-training-seed-repeat-materialization-result-audit.json`
- audited summary: `runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/summary.json`
- measured execution in M2178: `false`
- training/replay/PPO in M2178: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Materialization Audit

M2177 materialization is clean:

```text
result_class = current_sim_training_seed_repeat_materialization_pass
repeat_group_count = 3
existing_repeat_group_count = 1
new_repeat_group_count = 2
new_training_command_count = 14
successful_training_command_count = 14
failed_training_command_count = 0
new_materialized_workload_count = 640
checkpoint_path_missing_count = 0
checkpoint_path_exists_count = 640
reset_control_trained_count = 0
guardrail_violation_count = 0
```

The two new repeat workloads have the intended first-class repeat metadata:

```text
training_repeat_id
training_seed_group
profile_training_seed
profile_checkpoint_source_profile
checkpoint_materialization_mode
base_workload_id
```

## Readiness Blocker

M2178 identifies one remaining blocker before repeat measured execution:

```text
repeat metadata preservation gap:
  the repeat workloads include training_repeat_id and related fields,
  but paper_route_current_sim_controlled_comparison_measured_runner.py
  does not list those fields in WORKLOAD_METADATA_FIELDS / METADATA_FIELDS.
```

If measured execution runs now, episode rows will not carry the repeat group and
training seed metadata as first-class columns. That would make later seed-repeat
audit depend on parsing `workload_id`, which is weaker than the M2176 design.

## Decision

Decision:

```text
current_sim_repeat_materialization_audit_route_to_metadata_preserving_runner_design
```

The materialized repeat panel is valid, but repeat measured execution command
design remains blocked until the measured runner explicitly preserves repeat
metadata.

M2179 should design a small runner metadata extension:

```text
add repeat fields to WORKLOAD_METADATA_FIELDS / METADATA_FIELDS;
preserve them in measured episode and failure rows;
include them in metadata-missing validation for repeat workloads;
add focused fake-rollout tests;
do not run real measured execution;
do not rank profiles.
```

## Claim Boundary

Supported:

```text
The repeat checkpoint/workload panel is materialized and ready for a metadata
preservation repair.
```

Still unsupported:

```text
repeat measured execution;
profile ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```
