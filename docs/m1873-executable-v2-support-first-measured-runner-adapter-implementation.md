# M1873 Executable V2 Support-First Measured Runner Adapter Implementation

- status: completed
- decision: `support_first_measured_runner_adapter_implementation_pass_route_to_execution_design`
- branch: `paper_route_executable_v2_support_first_measured_execution`
- parent design: `docs/m1872-executable-v2-support-first-measured-runner-adapter-design.md`
- implementation: `src/autodrift/executable_v2_support_first_measured_runner_adapter.py`
- tests: `tests/test_executable_v2_support_first_measured_runner_adapter.py`
- project materialization run: false
- environment reset: false
- policy action executed: false
- measured rollout: false
- training/replay/PPO: false

## Purpose

M1873 implements the no-rollout adapter helper needed to convert support-first
executable-v2 specs into measured controller workload rows. It validates the
logic on fixtures only and does not run the real M1866/M1674 project
materialization.

## Implementation

The new module:

```text
src/autodrift/executable_v2_support_first_measured_runner_adapter.py
```

provides:

```text
load_support_first_executable_v2_specs
normalize_support_first_spec
normalize_support_first_specs
measured_workload_rows
run_support_first_measured_runner_adapter
```

The adapter writes these no-rollout artifacts when executed later:

```text
support_first_measured_executable_specs.json
support_first_measured_executable_specs.csv
support_first_measured_workload_matrix.csv
support_first_role_surface_counts.csv
controller_profile_artifact_rows.csv
support_first_measured_missing_field_rows.csv
support_first_measured_duplicate_key_rows.csv
support_first_measured_claim_boundary.csv
summary.json
```

It preserves the core semantic separation:

```text
scenario_profile_name = original support-first profile_name
controller_profile_name = controller-family policy profile
profile_name = controller_profile_name  # shared rollout helper compatibility
```

The pass logic rejects rows where `scenario_profile_name` is reused as the
controller policy profile.

## Focused Tests

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest -q tests/test_executable_v2_support_first_measured_runner_adapter.py
```

Result:

```text
4 passed in 0.92s
```

The focused tests cover:

- normalized specs and workload matrix writing on a small fixture;
- `profile_name == controller_profile_name` compatibility;
- original support-first profile name preserved only as `scenario_profile_name`;
- scenario-profile-as-controller violation rejection;
- duplicate spec id and missing required field rejection;
- target workload count equals `180 x 12 = 2160`.

## Claim Boundary

Supported by M1873:

```text
no-rollout adapter helper is implemented
fixture tests pass
scenario/controller profile separation is enforced
adapter execution design is admissible
```

Not supported by M1873:

```text
real M1866/M1674 adapter execution result
2160-cell workload matrix exists
measured rollout result
controller-family ranking
paper-level evidence
current-response / finite-window / GRU comparison result
level3 self-identification evidence
```

## Guardrails

- project materialization run: `false`
- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Decision

M1873 passes and routes to M1874 adapter execution design. M1874 should fix the
exact command for running the no-rollout adapter over the real M1866 support-
first payload and M1674 controller-family profile artifacts.
