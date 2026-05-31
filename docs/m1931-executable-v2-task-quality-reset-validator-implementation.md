# M1931 Executable V2 Task-Quality Reset Validator Implementation

- status: completed
- decision: `task_quality_reset_validator_implementation_pass_admit_command_design`
- branch: `paper_route_task_quality_reset_execution`
- source: `src/autodrift/executable_v2_task_quality_reset_validation_preflight.py`
- tests: `tests/test_executable_v2_task_quality_reset_validation_preflight.py`
- focused tests: `3 passed`
- real M1928 reset execution in M1931: `false`
- rollout/measured execution in M1931: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## What Changed

M1931 adds a focused reset-only validator for the M1928 task-quality scenario
redesign payload.

New helper:

```text
src/autodrift/executable_v2_task_quality_reset_validation_preflight.py
```

It consumes the exact M1928 payload shape:

```text
executable_task_specs
```

and intentionally avoids translating through the older
`executable_v2_panel_specs` schema. This keeps scenario metadata separate from
controller-family profile identity.

## Helper Behavior

The helper can:

- load and deterministically sort executable task specs;
- rebuild each embedded `env_config` through `build_env_config`;
- instantiate `AutoDriftEnv`;
- run one reset per task spec;
- preserve reset exceptions as failure rows;
- check finite observation and expected observation dimension;
- check obstacle initialization;
- write reset rows, failure rows, contract rows, aggregate rows, claim
  boundary, and summary artifacts;
- preserve reset-only guardrail flags.

The helper does not:

- load checkpoints;
- load controller profiles;
- execute policy actions;
- run rollout steps;
- run measured execution;
- train, replay, or run PPO;
- use private holdout;
- rank controller families;
- make paper-level or self-ID claims.

## Synthetic Test Coverage

Focused tests cover:

```text
task_quality_reset_validation_preflight_passes_on_synthetic_specs
task_quality_reset_validation_preflight_preserves_reset_failures
task_quality_reset_validation_preflight_fails_closed_on_contract_violation
```

Command:

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests/test_executable_v2_task_quality_reset_validation_preflight.py
```

Result:

```text
3 passed
```

The tests monkeypatch `AutoDriftEnv` with a fake environment. Therefore M1931
does not run real M1928 reset execution.

## Planned Real Reset Command

M1932 should freeze the real command before execution. The intended command is:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_reset_validation_preflight \
  --executable-task-specs runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json \
  --output-dir runs/m1933_executable_v2_task_quality_reset_validation_preflight \
  --eval-seed-base 193300 \
  --target-spec-count 80 \
  --expected-observation-dim 72 \
  --next-blocker m1934-executable-v2-task-quality-reset-validation-result-audit
```

M1932 should still be command design only. M1933 should be the first milestone
that runs real reset execution.

## Claim Boundary

M1931 supports only:

```text
task-quality reset validator infrastructure exists and has focused synthetic
tests.
```

It does not support:

- reset feasibility of the real M1928 panel;
- measured controller performance;
- controller ranking;
- policy improvement;
- finite-window vs GRU comparison;
- paper-level benchmark evidence;
- level3 self-identification evidence.

## Next

Next milestone:

```text
m1932-executable-v2-task-quality-reset-validation-command-design
```

M1932 should register the exact reset-only command, output directory, target
counts, artifact set, and pass/fail gates before M1933 runs real reset
validation.
