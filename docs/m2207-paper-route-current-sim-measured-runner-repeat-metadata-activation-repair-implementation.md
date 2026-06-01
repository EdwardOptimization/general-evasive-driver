# M2207 Paper-Route Current-Sim Measured-Runner Repeat-Metadata Activation Repair Implementation

- status: completed
- decision: `current_sim_measured_runner_repeat_metadata_activation_repair_pass_route_to_audit`
- manifest: `experiments/manifests/m2207-paper-route-current-sim-measured-runner-repeat-metadata-activation-repair-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_controlled_comparison_measured_runner.py`
- focused tests: `4 passed`
- no-rollout metadata check over M2194/M2200: `metadata_missing_rows=0`, `validation_failure_rows=0`
- measured execution in M2207: `false`
- policy action executed in M2207: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## What Changed

M2207 implements the M2206 activation design.

Repeat identity fields are now separate from checkpoint provenance:

```text
REPEAT_IDENTITY_WORKLOAD_METADATA_FIELDS:
  training_repeat_id
  training_seed_group
  profile_training_seed
  profile_checkpoint_source_profile
  base_workload_id

OPTIONAL_REPEAT_WORKLOAD_METADATA_FIELDS:
  training_repeat_id
  training_seed_group
  profile_training_seed
  profile_checkpoint_source_profile
  checkpoint_materialization_mode
  base_workload_id
```

Repeat mode is activated only by repeat identity fields:

```text
_has_repeat_metadata(row)
  -> any(non-empty repeat identity field)
```

If repeat mode is active, all optional repeat workload fields are still
required, including `checkpoint_materialization_mode`. If repeat mode is not
active, `checkpoint_materialization_mode` can remain non-empty and is preserved
as checkpoint provenance.

## Focused Tests

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_controlled_comparison_measured_runner.py
```

Result:

```text
4 passed
```

Coverage:

```text
non-repeat fake rollout with checkpoint_materialization_mode passes;
complete repeat metadata fake rollout passes and writes training_repeat_aggregate.csv;
partial repeat identity metadata fails closed before rollout;
missing checkpoint path fails closed.
```

## No-Rollout Artifact Check

Command:

```bash
PYTHONPATH=src python - <<'PY'
from autodrift.paper_route_current_sim_controlled_comparison_measured_runner import (
    load_executable_task_specs,
    load_workload_rows,
    metadata_missing_rows,
    validation_failure_rows,
)
specs = load_executable_task_specs('runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/repaired_executable_task_specs.json')
workload = load_workload_rows('runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/materialized_workload.csv')
print(len(metadata_missing_rows(executable_specs=specs, workload_rows=workload)))
print(len(validation_failure_rows(executable_specs=specs, workload_rows=workload, require_checkpoint_paths=True)))
PY
```

Result:

```text
metadata_missing_rows=0
validation_failure_rows=0
```

This check does not execute policy actions or start environment rollout.

## Claim Boundary

Supported by M2207:

```text
The measured runner no longer treats checkpoint_materialization_mode alone as
repeat-mode activation, while partial repeat identity metadata still fails
closed.
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

M2208 must audit this implementation before a measured-execution rerun is
admitted.
