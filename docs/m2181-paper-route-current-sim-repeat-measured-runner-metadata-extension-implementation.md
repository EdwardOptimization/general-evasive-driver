# M2181 Paper-Route Current-Sim Repeat Measured-Runner Metadata Extension Implementation

- status: completed
- decision: `current_sim_repeat_metadata_extension_implementation_pass_route_to_audit`
- manifest: `experiments/manifests/m2181-paper-route-current-sim-repeat-measured-runner-metadata-extension-implementation.json`
- focused tests: `4 passed`
- training in M2181: `false`
- measured execution in M2181: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## What Changed

M2181 implements the M2179/M2180 metadata blocker repair in:

```text
src/autodrift/paper_route_current_sim_controlled_comparison_measured_runner.py
tests/test_paper_route_current_sim_controlled_comparison_measured_runner.py
```

The measured runner now treats these repeat workload fields as optional repeat
metadata:

```text
training_repeat_id
training_seed_group
profile_training_seed
profile_checkpoint_source_profile
checkpoint_materialization_mode
base_workload_id
```

Compatibility rule implemented:

```text
Non-repeat workloads remain valid without repeat fields.

If any repeat metadata value is non-empty for a workload row, all repeat
metadata fields must be non-empty for that row before rollout may start.
```

The metadata row builder now writes the repeat fields into episode/failure rows
when present. The finalizer writes `training_repeat_aggregate.csv` only when
episode rows contain non-empty `training_repeat_id` values.

## Validation

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_controlled_comparison_measured_runner.py
```

Result:

```text
4 passed in 2.17s
```

Focused coverage:

```text
non-repeat fake rollout remains accepted;
repeat fake rollout preserves repeat metadata in episode rows;
repeat fake rollout creates training_repeat_aggregate.csv;
partial repeat metadata fails validation before rollout;
missing checkpoint fail-closed path remains intact.
```

## Claim Boundary

Allowed claim:

```text
The current-sim measured runner preserves repeat metadata under focused
fake-rollout tests while keeping non-repeat workloads backward compatible.
```

Still not allowed:

```text
repeat measured execution result;
profile ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next Step

M2182 must audit this implementation before any repeat measured-execution
command design or rollout. If the audit accepts the patch, the next branch step
can freeze a repeat measured-execution command that preserves
`training_repeat_id` and seed metadata end to end.
