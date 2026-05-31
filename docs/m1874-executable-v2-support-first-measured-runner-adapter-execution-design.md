# M1874 Executable V2 Support-First Measured Runner Adapter Execution Design

- status: completed
- decision: `support_first_measured_runner_adapter_execution_design_admit_preflight_run`
- branch: `paper_route_executable_v2_support_first_measured_execution`
- parent implementation: `docs/m1873-executable-v2-support-first-measured-runner-adapter-implementation.md`
- adapter: `src/autodrift/executable_v2_support_first_measured_runner_adapter.py`
- no execution in M1874: true
- environment reset: false
- policy action executed: false
- measured rollout: false
- training/replay/PPO: false

## Purpose

M1874 fixes the exact no-rollout adapter execution command over the real M1866
support-first payload and M1674 controller-family profile artifacts. It does
not run the command.

## Fixed Inputs

Support-first reset-validated executable-v2 payload:

```text
runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_executable_v2_panel_specs.json
```

Controller-family public pilot artifacts:

```text
runs/m1674_controller_family_one_seed_public_pilot/configs/*_seed167400.json
runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
```

## Exact Command For M1875

M1875 should run exactly:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_support_first_measured_runner_adapter \
  --executable-v2-panel-specs runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_executable_v2_panel_specs.json \
  --m1674-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --profile-seed 167400 \
  --output-dir runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight \
  --target-support-first-spec-count 180 \
  --target-controller-profile-count 12 \
  --target-workload-cell-count 2160 \
  --target-role-count 4 \
  --target-role-surface-count 8 \
  --next-blocker m1876-executable-v2-support-first-measured-runner-adapter-result-audit
```

This command must only materialize normalized adapter artifacts. It must not
create an environment, reset the environment, execute policy actions, or run
measured rollout.

## Required M1875 Artifacts

M1875 should write:

```text
runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/summary.json
runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_executable_specs.json
runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_executable_specs.csv
runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_workload_matrix.csv
runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_role_surface_counts.csv
runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/controller_profile_artifact_rows.csv
runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_missing_field_rows.csv
runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_duplicate_key_rows.csv
runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_claim_boundary.csv
```

## M1875 Pass Criteria

M1875 passes only if `summary.json` reports:

```text
result_class: executable_v2_support_first_measured_runner_adapter_pass
support_first_spec_count: 180
controller_profile_count: 12
workload_cell_count: 2160
role_count: 4
role_surface_count: 8
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
missing_profile_artifact_count: 0
profile_alias_mismatch_count: 0
scenario_as_controller_profile_count: 0
missing_required_field_count: 0
duplicate_key_count: 0
guardrail_violation_count: 0
environment_reset_started: false
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

The result must also preserve the known role-surface imbalance rather than
hiding it behind aggregate counts.

## Failure Routing

If M1875 fails because profile artifacts are missing, route to profile artifact
inventory/repair. If it fails because scenario/controller profile semantics
are conflated, route to adapter schema repair. If it passes, route to M1876
result audit before any measured rollout design.

## Claim Boundary

Supported by M1874:

```text
exact no-rollout adapter execution command is registered
target counts and output directory are fixed
adapter execution is admissible as M1875
```

Not supported by M1874:

```text
adapter execution result
2160-cell workload matrix exists
environment reset or rollout result
measured controller comparison
controller-family ranking
paper-level evidence
level3 self-identification evidence
```

## Guardrails

- adapter execution run in M1874: `false`
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

Admit M1875 no-rollout support-first measured-runner adapter preflight.
