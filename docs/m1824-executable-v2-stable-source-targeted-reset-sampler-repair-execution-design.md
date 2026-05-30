# M1824 Executable V2 Stable Source Targeted Reset Sampler Repair Execution Design

- status: completed
- decision: `stable_source_targeted_reset_sampler_repair_execution_design_admit_no_reset_run`
- source implementation: `src/autodrift/executable_v2_stable_source_targeted_reset_sampler_repair.py`
- project artifact repair run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1823 implemented the no-reset repair planner. M1824 pre-registers the exact
command to run that planner over the project artifacts from M1816 and M1820.
This milestone does not run the planner and does not run reset.

## Input Artifacts

```text
runs/m1816_executable_v2_stable_source_reset_validation_adapter/targeted_reset_executable_v2_panel_specs.json
runs/m1820_executable_v2_stable_source_targeted_reset_feasibility_preflight/reset_stress_rows.csv
```

## Output Directory

```text
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair
```

## Exact M1825 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_stable_source_targeted_reset_sampler_repair \
  --targeted-reset-specs runs/m1816_executable_v2_stable_source_reset_validation_adapter/targeted_reset_executable_v2_panel_specs.json \
  --reset-rows runs/m1820_executable_v2_stable_source_targeted_reset_feasibility_preflight/reset_stress_rows.csv \
  --output-dir runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair \
  --target-repair-source-count 3 \
  --target-profile-count 12 \
  --target-repaired-spec-count 36 \
  --next-blocker m1826-executable-v2-stable-source-targeted-reset-sampler-repair-result-audit
```

This command must not call `env.reset`.

## Expected Counts

M1825 should pass only if:

| field | expected |
| --- | ---: |
| `repair_target_source_count` | 3 |
| `systematic_source_count` | 2 |
| `sparse_source_count` | 1 |
| `profile_control_count` | 12 |
| `repaired_executable_spec_count` | 36 |
| `reset_ready_spec_count` | 36 |
| `labels_enter_actor_input_count` | 0 |
| `ranking_admissible_by_default_count` | 0 |
| `guardrail_violation_count` | 0 |

Expected output artifacts:

```text
summary.json
source_sampler_repair_targets.csv
source_sampler_repair_specs.json
source_sampler_repair_specs.csv
source_sampler_repair_matrix.csv
repaired_targeted_reset_executable_v2_panel_specs.json
source_sampler_repair_claim_boundary.csv
```

## Follow-Up

If M1825 passes, route to:

```text
m1826-executable-v2-stable-source-targeted-reset-sampler-repair-result-audit
```

The audit should decide whether to design a reset-only preflight over:

```text
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json
```

## Guardrails

- project artifact repair run: `false`
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

## Claim Boundary

Supported:

- exact no-reset repair planner command;
- input artifacts, output directory, target counts, and next blocker.

Unsupported:

- project repair execution result;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
