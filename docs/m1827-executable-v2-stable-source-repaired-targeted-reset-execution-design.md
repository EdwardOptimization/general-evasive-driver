# M1827 Executable V2 Stable Source Repaired Targeted Reset Execution Design

- status: completed
- decision: `stable_source_repaired_targeted_reset_execution_design_admit_preflight_run`
- branch: `paper_route_executable_v2_targeted_reset_validation`
- source payload: `runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json`
- reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1826 audited the M1825 repaired payload as complete and reset-ready. M1827
pre-registers the exact M1792-compatible reset-only command over that repaired
payload. This milestone does not run reset.

## Input Payload

```text
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json
```

Expected payload:

```text
executable_v2_panel_specs: 36 rows
profiles: 12
role surfaces: 1
role surface: stable_avoidance_aes
labels: aes_feasible=24, aeb_feasible=12
reset_ready_spec_count=36
```

## Output Directory

```text
runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight
```

## Exact M1828 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_reset_feasibility_preflight \
  --executable-v2-panel-specs runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json \
  --output-dir runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight \
  --eval-seed-base 182800 \
  --target-spec-count 36 \
  --target-profile-count 12 \
  --target-role-surface-count 1 \
  --next-blocker m1829-executable-v2-stable-source-repaired-targeted-reset-feasibility-result-audit
```

This command may instantiate `AutoDriftEnv` and call `env.reset`. It must not
step the environment or execute a policy action.

## Expected Counts

M1828 should pass only if:

| field | expected |
| --- | ---: |
| `attempted_spec_count` | 36 |
| `reset_success_count` | 36 |
| `sampling_failure_count` | 0 |
| `profile_count` | 12 |
| `role_surface_count` | 1 |
| `reset_ready_spec_count` | 36 |
| `labels_enter_actor_input_count` | 0 |
| `ranking_admissible_by_default_count` | 0 |
| `metadata_join_incomplete_count` | 0 |
| `guardrail_violation_count` | 0 |

Expected task-label support:

```text
aeb_feasible: 12
aes_feasible: 24
```

Expected artifacts:

```text
summary.json
reset_stress_rows.csv
sampling_failure_rows.csv
label_distribution_by_surface.csv
label_distribution_by_profile.csv
label_distribution_by_hidden_bucket.csv
```

## Pass Criteria

M1828 passes if the adapter result class is:

```text
executable_v2_reset_feasibility_preflight_pass
```

and all expected counts match. A pass would support repaired targeted reset
feasibility for these 36 rows only. It still would not admit measured execution
or controller-family ranking without a result audit and execution-design
milestone.

## Failure Handling

If M1828 fails, the result should be audited rather than repaired in-place.
Likely failure classes:

- `scenario_sampling_failure`: a repaired stable source still cannot sample the
  requested label under reset.
- `metric_artifact`: metadata/count mismatch or guardrail inconsistency.

## Guardrails

- environment reset started: `false` in M1827 design;
- environment rollout started: `false`;
- policy action executed: `false`;
- measured rollout started: `false`;
- training started: `false`;
- replay started: `false`;
- PPO used: `false`;
- promoted: `false`;
- private holdout used: `false`;
- actor input contract changed: `false`;
- reward changed: `false`;
- dynamics changed: `false`;
- termination behavior changed: `false`;
- profile-specific tuning: `false`;
- controller-family ranking claim made: `false`;
- paper-level claim made: `false`;
- level3 self-ID claim made: `false`;
- guardrail violation count: `0`.

## Claim Boundary

Supported:

- exact repaired targeted reset-only command and expected counts;
- M1828 reset-only execution is admitted.

Unsupported:

- repaired targeted reset validation result;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
