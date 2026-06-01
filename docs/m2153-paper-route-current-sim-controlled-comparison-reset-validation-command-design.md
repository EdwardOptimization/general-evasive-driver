# M2153 Paper-Route Current-Sim Controlled Comparison Reset Validation Command Design

- status: completed
- decision: `current_sim_reset_validation_command_design_admit_implementation_and_run`
- parent artifact: `runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json`
- reset/rollout/measured execution in M2153: `false`
- policy actions executed in M2153: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Constraint

M2152 audited M2151 as a clean no-rollout executable-spec
materialization. The artifact is now concrete enough for reset validation, but
it uses current-sim-specific semantics:

```text
materialization_semantics == current_sim_executable_spec_v0
target_executable_spec_count == 40
expected_observation_dim == 72
task families == T1-T5
profiles == 8
```

M2154 should therefore implement a current-sim-specific reset validator that
reuses the low-level reset helper where possible, accepts the M2151 semantics,
and preserves task-family, source-family-template, profile, and claim-boundary
metadata. It must not use the older comparison-support validator directly
because that validator was tied to a different materialization semantic and
metadata schema.

## Frozen Command

M2154 must implement and run exactly:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_controlled_comparison_reset_validation_preflight \
  --executable-task-specs runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json \
  --output-dir runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight \
  --eval-seed-base 215300 \
  --target-spec-count 40 \
  --expected-observation-dim 72 \
  --next-blocker m2155-paper-route-current-sim-controlled-comparison-reset-validation-result-audit
```

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_controlled_comparison_reset_validation_preflight.py
```

## Planned Artifacts

M2154 must write:

```text
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/summary.json
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/reset_rows.csv
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/reset_failure_rows.csv
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/contract_rows.csv
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/reset_distribution_by_task_family.csv
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/reset_distribution_by_source_family_template.csv
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/metadata_missing_rows.csv
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/claim_boundary.csv
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/run_state.json
```

## Pass Gates

M2154 passes only if:

```text
result_class == current_sim_controlled_comparison_reset_validation_preflight_pass
input_executable_spec_count == 40
target_executable_spec_count == 40
reset_attempt_count == 40
reset_success_count == 40
reset_failure_count == 0
observation_dimension_failure_count == 0
observation_finite_count == 40
obstacle_initialized_count == 40
contract_violation_count == 0
metadata_missing_count == 0
forbidden_key_violation_count == 0
task_family_quota_pass == true
source_family_template_quota_pass == true
guardrail_violation_count == 0
```

Reset validation may claim only scenario reset admissibility if audited later.
It remains non-comparison evidence.

## Claim Boundary

Supported after a clean M2154 run and M2155 audit:

```text
current-sim controlled-comparison executable specs reset successfully with
finite 72-dimensional observations and initialized obstacles.
```

Unsupported:

```text
measured execution;
policy behavior;
controller-family ranking;
winner selection;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2154-paper-route-current-sim-controlled-comparison-reset-validation-implementation-and-run
```
