# M2206 Paper-Route Current-Sim Measured-Runner Repeat-Metadata Activation Repair Design

- status: completed
- decision: `current_sim_measured_runner_repeat_metadata_activation_repair_design_admit_implementation`
- manifest: `experiments/manifests/m2206-paper-route-current-sim-measured-runner-repeat-metadata-activation-repair-design.json`
- parent audit: `docs/m2205-paper-route-current-sim-offtrack-support-measured-execution-result-audit.md`
- implementation in M2206: `false`
- measured execution in M2206: `false`
- policy action executed in M2206: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2206 fixes the design boundary exposed by M2204/M2205:

```text
checkpoint_materialization_mode is checkpoint provenance.
It is not sufficient evidence that a workload row belongs to a training-repeat panel.
```

The measured runner should keep M2181's compatibility intent:

```text
non-repeat workload without repeat identity metadata remains valid;
repeat workload preserves repeat metadata and writes repeat aggregate;
partial repeat identity metadata fails closed before rollout.
```

## Activation Rule

Split repeat metadata into two groups:

```text
repeat identity fields:
  training_repeat_id
  training_seed_group
  profile_training_seed
  profile_checkpoint_source_profile
  base_workload_id

checkpoint provenance field:
  checkpoint_materialization_mode
```

Repeat mode is activated only if any repeat identity field is non-empty:

```text
has_repeat_identity_metadata =
  any(training_repeat_id,
      training_seed_group,
      profile_training_seed,
      profile_checkpoint_source_profile,
      base_workload_id)
```

When repeat mode is active, all repeat identity fields and
`checkpoint_materialization_mode` must be non-empty:

```text
required_repeat_fields =
  repeat identity fields
  + checkpoint_materialization_mode
```

When repeat mode is not active, `checkpoint_materialization_mode` may still be
non-empty and should be preserved in metadata rows. It must not trigger a
missing-repeat-metadata failure by itself.

## Code Scope

Allowed implementation files:

```text
src/autodrift/paper_route_current_sim_controlled_comparison_measured_runner.py
tests/test_paper_route_current_sim_controlled_comparison_measured_runner.py
```

Expected code changes:

```text
define REPEAT_IDENTITY_WORKLOAD_METADATA_FIELDS
keep OPTIONAL_REPEAT_WORKLOAD_METADATA_FIELDS for row output schema
change _has_repeat_metadata to check only identity fields
change _missing_repeat_metadata_fields to require identity fields plus checkpoint_materialization_mode only when identity fields activate repeat mode
preserve current_sim_metadata_row output fields
preserve training_repeat_aggregate only when episode rows contain training_repeat_id
```

Do not change actor inputs, profile configs, task specs, workload rows,
checkpoint paths, or measured-runner output schema.

## Required Tests

Focused tests must cover:

```text
1. non-repeat workload with checkpoint_materialization_mode passes fake rollout;
2. repeat workload with all repeat identity fields passes and writes training_repeat_aggregate.csv;
3. partial repeat identity metadata still fails closed before rollout;
4. missing checkpoint path still fails closed.
```

Existing tests already cover cases 2-4. M2207 should add or extend a focused
test for case 1.

## Rejected Designs

Rejected:

```text
add fake repeat IDs to M2200 workload rows
```

Reason: this would make non-repeat workload look like repeat workload and could
pollute repeat aggregate semantics.

Rejected:

```text
remove checkpoint_materialization_mode from M2200 workload rows
```

Reason: this removes useful checkpoint provenance and weakens downstream
episode metadata.

Rejected:

```text
disable repeat metadata validation entirely
```

Reason: partial repeat metadata should still fail closed before rollout.

## Claim Boundary

Allowed claim after M2207 implementation:

```text
The current-sim measured runner treats checkpoint_materialization_mode as
checkpoint provenance and preserves M2181 repeat compatibility semantics.
```

Still blocked:

```text
M2204 rerun;
measured rollout success;
controller-family ranking;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next Step

M2207 may implement the focused repair and tests. A repaired measured-execution
rerun is still blocked until M2207 is implemented, validated, reviewed, and
audited or explicitly admitted by the follow-up route.
