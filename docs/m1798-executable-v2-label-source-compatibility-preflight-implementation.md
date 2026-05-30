# M1798 Executable V2 Label-Source Compatibility Preflight Implementation

- status: completed
- decision: `label_source_compatibility_preflight_implementation_pass_route_to_execution_design`
- module: `src/autodrift/executable_v2_label_source_compatibility_preflight.py`
- test: `tests/test_executable_v2_label_source_compatibility_preflight.py`
- focused test command: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest tests/test_executable_v2_label_source_compatibility_preflight.py -q`
- focused test result: `2 passed in 0.06s`
- project artifact execution: `false`
- reset run: `false`
- rollout started: `false`
- training/replay/PPO: `false`

## Summary

M1798 implements the no-reset compatibility helper designed in M1797. The helper
reads executable v2 specs and reset result rows, then writes source-label support
and quarantine artifacts without touching the environment.

The implementation supports these group-level source-label statuses:

```text
supported_observed
unsupported_systematic
sparse_fragile
unobserved
```

It also preserves row-level compatibility: observed reset-success rows remain
eligible for a later reset-rerun subset, while systematic failures and sparse
failed rows are quarantined. Measured execution and controller-family ranking
remain blocked regardless of row-level compatibility.

## Implemented Artifacts

The helper writes:

```text
summary.json
source_label_support.csv
compatibility_violation_rows.csv
sparse_failure_rows.csv
unobserved_rows.csv
replacement_need_rows.csv
compatible_executable_v2_panel_specs.json
compatible_executable_v2_panel_specs.csv
compatible_executable_v2_panel_matrix.csv
claim_boundary.csv
```

The compatible JSON keeps the same top-level key expected by the v2 reset
adapter:

```text
executable_v2_panel_specs
```

Extra compatibility fields are additive metadata. `env_config`, profile names,
role-surface fields, task labels, hidden buckets, and v2 metric fields are
preserved.

## Focused Test Coverage

The focused fixture covers:

- a `supported_observed` source-label group;
- an `unsupported_systematic` group where all profiles fail;
- a `sparse_fragile` group where one profile fails and other profiles succeed;
- an `unobserved` spec with no reset row;
- compatible-spec JSON preservation;
- violation, sparse, replacement, support, and claim-boundary outputs;
- labels not entering actor input;
- ranking and measured execution remaining blocked.

No project artifact execution, reset, rollout, policy action, training, replay,
or PPO occurred.

## Route Decision

Route to:

```text
m1799-executable-v2-label-source-compatibility-preflight-execution-design
```

M1799 should fix the exact command to run the helper on M1790/M1794 artifacts
and define expected counts before execution. The execution milestone should be
separate from this implementation milestone.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- project artifact execution: `false`
- policy action executed: `false`
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

- no-reset compatibility helper implementation;
- focused tests for support, violation, sparse, and unobserved cases;
- compatibility artifact shape for a later execution milestone.

Unsupported:

- M1790/M1794 compatibility execution result;
- repaired reset feasibility pass;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
