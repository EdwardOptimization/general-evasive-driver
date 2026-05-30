# M1836 Executable V2 Reset-Time AES Source Repair V2 Implementation

- status: completed
- decision: `reset_time_aes_source_repair_v2_implementation_pass_route_to_execution_design`
- branch: `paper_route_executable_v2_reset_time_aes_source_repair_v2`
- source: `src/autodrift/executable_v2_reset_time_aes_source_repair_v2.py`
- test: `tests/test_executable_v2_reset_time_aes_source_repair_v2.py`
- project artifact execution: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1836 implements the no-reset helper designed in M1835. The helper scores
source-level AES repair candidates by replaying reset-time obstacle sampler
attempts from reset RNG state. It selects only source-level patches and writes
row-count plus attempt-count aggregations so the M1834 summary metric artifact
does not repeat.

This milestone does not run the helper on project artifacts. It adds the helper
and focused tests only.

## Implementation

Added:

```text
src/autodrift/executable_v2_reset_time_aes_source_repair_v2.py
tests/test_executable_v2_reset_time_aes_source_repair_v2.py
```

The helper reuses:

```text
autodrift.executable_v2_reset_time_aes_sampler_diagnostic.replay_reset_time_obstacle_attempts
autodrift.executable_v2_reset_time_aes_sampler_diagnostic.summarize_attempts
autodrift.executable_v2_stable_source_targeted_reset_sampler_repair.label_density
```

It does not call `AutoDriftEnv.reset`, step an environment, execute a policy
action, train, replay, or run PPO.

## Helper Behavior

For each failed AES source group:

1. collect failed `aes_feasible` rows from reset rows;
2. generate source-level obstacle candidates;
3. score candidates by reset-time sampler replay;
4. select the candidate with highest accepted profile count and tie-breakers;
5. apply the selected patch to all profiles for that source;
6. pass unchanged non-target sources through;
7. write a repaired executable v2 payload for later reset-only validation.

Primary acceptance objective:

```text
accepted_profile_count == profile_count
label == "aes_feasible"
reject_reason == "accepted"
require_aeb_infeasible == true
```

The selected candidate summary writes both:

```text
attempt_count_by_label
attempt_count_by_reject_reason
row_count_by_label
row_count_by_reject_reason
summary_aggregation_version = "row_and_attempt_counts_v1"
```

## Focused Tests

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest tests/test_executable_v2_reset_time_aes_source_repair_v2.py -q
```

Result:

```text
3 passed in 0.12s
```

Coverage:

- an AEB-feasible-only candidate is rejected and not selected;
- a reset-time AES-only source candidate is selected;
- profile controls are source-level, not profile-specific;
- unchanged AEB rows are passed through;
- row and attempt aggregations are written;
- reset feasibility and ranking claims remain blocked.

## Full Test Run

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q
```

Result:

```text
1745 passed, 4 warnings in 10.23s
```

Warnings are the existing multiprocessing fork deprecation warnings from vector
env tests.

## Guardrails

- project artifact repair execution: `false`
- environment reset started: `false`
- environment rollout started: `false`
- measured rollout started: `false`
- policy action executed: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- helper implementation and focused tests;
- full pytest non-regression;
- execution design is admitted.

Unsupported:

- project artifact repair result;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.

## Follow-Up

Route to:

```text
m1837-executable-v2-reset-time-aes-source-repair-v2-execution-design
```

M1837 should pre-register the exact command to run the helper on M1825/M1828
artifacts. It should not run the command.
