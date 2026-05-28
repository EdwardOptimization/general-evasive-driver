# M1182 No-Residual Source-Rich Adapter Implementation

## Summary

M1182 implements a current public-base source-rich adapter that does not
require or load a residual head. The new module is:

```text
src/autodrift/current_base_source_rich_adapter.py
```

Focused tests are:

```text
tests/test_current_base_source_rich_adapter.py
```

This is infrastructure only. It does not run source-rich mining, full replay,
actor training, PPO, promotion, private holdout, row conversion, or actor-input
changes.

## Why This Was Needed

M1181 found that the existing v4 source-rich route tools were built around an
M568 actor plus M761 residual head route. The current public-gate base uses a
12-feature actor head while the old residual head expects feature dimension
64, so the old route cannot be used for current-base evidence. Using
`alpha=0` is not a workaround because the residual head is loaded before alpha
can neutralize residual action.

M1182 therefore adds a small adapter that evaluates the loaded current actor
directly.

## Implemented Interface

The adapter CLI accepts:

```text
python -m autodrift.current_base_source_rich_adapter \
  --checkpoint <current-base-checkpoint> \
  --scenario-config configs/cross_fault_hidden_condition_scenarios.json \
  --run-dir <run-dir>
```

It intentionally has no `--residual-head` argument.

The adapter writes:

```text
summary.json
source_group_rows.csv
warmup_probe_rows.csv
source_result_rows.csv
boundary_search_plan_rows.csv
fault_proxy_limitations.md
progress.jsonl
```

## Metadata Contract

The adapter emits or validates source-rich metadata needed by later smoke runs:

```text
policy_label
residual_head_required
seed
step
warmup_mode
preferred_fault
preferred_fault_family
preferred_fault_severity
preferred_fault_fidelity_class
wrong_fault
wrong_fault_family
wrong_fault_fidelity_class
fault_family_pair
source_axis
fault_onset_bucket
source_obstacle_body_x
source_obstacle_body_y
source_obstacle_half_width
target_obstacle_body_x
target_obstacle_body_y
target_obstacle_half_width
boundary_axis
source_margin
source_success
source_collision
source_terminal_reason
current_frame_match_status
action_divergence_status
terminal_margin_sensitivity_status
```

The last three fields are intentionally marked `not_computed_in_adapter`; they
belong to later matched-current and action-divergence stages. M1182 only
ensures the fields are present so later artifacts cannot lose the source-rich
schema again.

## Verification

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_current_base_source_rich_adapter.py
```

Result:

```text
5 passed
```

Research validation:

```text
make research-validate
```

Result:

```text
research validation passed
```

## Decision

```text
current_base_no_residual_source_rich_adapter_implemented_route_to_smoke_run
```

M1183 may run a small metadata smoke using the adapter. M1183 must still avoid
training, PPO, promotion, private holdout, proof conversion, and paper-level
claims.
