# M2179 Paper-Route Current-Sim Repeat Measured-Runner Metadata Extension Design

- status: completed
- decision: `current_sim_repeat_metadata_extension_design_admit_required_branch_synthesis`
- manifest: `experiments/manifests/m2179-paper-route-current-sim-repeat-measured-runner-metadata-extension-design.json`
- training in M2179: `false`
- measured execution in M2179: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2178 audits repeat materialization as clean but blocks repeat measured
execution because the current measured runner does not preserve repeat metadata
from workload rows into episode/failure rows.

M2179 freezes the narrow runner metadata extension required before repeat
rollout.

## Required Repeat Fields

The repeat materializer writes these workload fields:

```text
training_repeat_id
training_seed_group
profile_training_seed
profile_checkpoint_source_profile
checkpoint_materialization_mode
base_workload_id
```

These fields must become first-class metadata in measured episode and failure
rows when present in the workload.

## Compatibility Rule

Do not make repeat fields globally required for older non-repeat workloads.

Instead:

```text
If a workload row includes any repeat metadata field, all repeat metadata fields
must be preserved and must be non-empty for that row.

If a workload row includes no repeat metadata fields, the runner should behave
as before.
```

This avoids breaking the already valid M2174 non-repeat measured execution path.

## Implementation Scope for M2180

The next implementation milestone should update:

```text
src/autodrift/paper_route_current_sim_controlled_comparison_measured_runner.py
tests/test_paper_route_current_sim_controlled_comparison_measured_runner.py
```

Required code behavior:

```text
define OPTIONAL_REPEAT_WORKLOAD_METADATA_FIELDS;
include repeat fields in current_sim_metadata_row when present;
require all repeat fields when any repeat field is present;
write repeat fields into episode_rows.csv under fake rollout;
write repeat fields into failure_rows.csv if rollout fails;
add training_repeat_aggregate.csv when episode rows contain training_repeat_id.
```

The implementation must not:

```text
run real measured execution;
change actor inputs;
change profile definitions;
rank profiles;
claim paper-level evidence;
claim finite-window vs GRU;
claim level3 self-identification.
```

## Focused Tests

The implementation tests should cover:

```text
1. fake-rollout repeat workload preserves training_repeat_id and related fields
   in episode rows and creates a training_repeat_aggregate artifact.

2. repeat workload with a missing repeat field fails validation before rollout.

3. non-repeat workload remains accepted without repeat fields.
```

## Claim Boundary

Allowed after implementation:

```text
The current-sim measured runner can preserve repeat-seed metadata under focused
fake-rollout tests.
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

The workflow synthesis cadence is now reached. M2180 must first synthesize the
repeat-readiness branch before implementation continues. If that synthesis
decision is `continue`, the following milestone may implement the metadata
extension and run focused tests only. Real repeat measured execution remains
blocked until the implementation result is audited.
