# M1965 Executable V2 Task-Quality Calibrated Materialization Branch Synthesis

- status: completed
- synthesis decision: `continue`
- completed branch segment: `paper_route_task_quality_calibrated_materialization`
- decision: `task_quality_calibrated_materialization_branch_synthesis_continue_to_measured_execution`
- reset/rollout/measured execution in M1965: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M1955-M1964 turned the calibrated source-mining pass from M1952 into a bounded,
reset-valid, metadata-preserving measured execution panel. The branch did not
run measured rollout, controller-family ranking, training, replay, or PPO.

Branch progression:

```text
M1955: designed an 80-source calibrated materialization subset
M1956: implemented and ran deterministic selector
M1957: audited preflight route; generic M1928 preflight was not schema-exact
M1958: implemented and ran focused no-reset materialization preflight
M1959: froze focused reset-only validation command
M1960: ran reset-only validation over the 80 executable specs
M1961: audited reset validation as clean
M1962: audited measured runner route; legacy M1936 runner lacked metadata fields
M1963: implemented calibrated measured runner adapter with focused tests
M1964: froze measured execution command and pass gates
```

Material evidence changed:

```text
before M1955:
  calibrated source-mining support existed, but no bounded executable panel
  had been selected, materialized, reset-validated, or command-designed.

after M1964:
  the branch has 80 selected supported sources, 960 planned workload cells,
  80/80 reset validity, a calibrated metadata-preserving measured runner,
  and a frozen measured execution route.
```

Selector evidence:

```text
M1956 result_class: task_quality_calibrated_materialization_selector_pass
selected_source_count: 80
selected_supported_source_count: 80
eligible_source_count: 130
expected_planned_workload_cell_count: 960
source_kind_quota_pass: true
role_surface_quota_pass: true
guardrail_violation_count: 0
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
profile_specific_tuning_count: 0
```

Selected source-kind counts:

```text
anchor_neighborhood: 32
success_stabilizer: 24
offtrack_boundary_relief: 8
mitigation_isolation_check: 16
```

Selected role counts:

```text
stable_aeb: 44
stable_aes_only: 14
drift_required_recovery: 9
unavoidable_mitigation: 13
```

Calibrated anchor and success-stabilizer provenance remains balanced:

```text
calibrated_anchor_selected_count: 32
calibrated_anchor_post_friction_step_selected_count: 16
calibrated_anchor_steady_surface_selected_count: 16
success_stabilizer_post_friction_step_selected_count: 12
success_stabilizer_steady_surface_selected_count: 12
```

No-reset materialization evidence:

```text
M1958 result_class: task_quality_calibrated_materialization_preflight_pass
executable_task_spec_count: 80
planned_workload_cell_count: 960
controller_profile_count: 12
selected_accepted_cell_row_count: 3382
missing_accepted_cell_count: 0
materialization_failure_count: 0
duplicate_task_source_id_count: 0
duplicate_workload_key_count: 0
contract_violation_count: 0
forbidden_key_violation_count: 0
missing_profile_artifact_count: 0
source_kind_quota_pass: true
role_surface_quota_pass: true
guardrail_violation_count: 0
```

Reset validation evidence:

```text
M1960 result_class: task_quality_calibrated_reset_validation_preflight_pass
reset_attempt_count: 80
reset_success_count: 80
reset_failure_count: 0
observation_finite_count: 80
observation_dimension_failure_count: 0
obstacle_initialized_count: 80
contract_violation_count: 0
label_actor_input_violation_count: 0
forbidden_key_violation_count: 0
source_kind_quota_pass: true
role_surface_quota_pass: true
guardrail_violation_count: 0
```

Measured execution readiness:

```text
M1963 focused tests: 3 passed
M1963 real measured execution: false
M1964 real measured execution: false
target episode_count: 960
target spec_count: 80
target profile_count: 12
device: cpu
eval_seed_base: 196500
```

M1964 froze the measured execution route. Because this synthesis is inserted by
workflow cadence, M1966 should execute the same semantic command with the
output directory and next blocker renumbered for artifact hygiene:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_measured_runner \
  --executable-task-specs runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json \
  --workload runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv \
  --output-dir runs/m1966_executable_v2_task_quality_calibrated_measured_execution \
  --eval-seed-base 196500 \
  --device cpu \
  --target-episode-count 960 \
  --target-spec-count 80 \
  --target-profile-count 12 \
  --next-blocker m1967-executable-v2-task-quality-calibrated-measured-execution-result-audit
```

## Supported Claims

Supported task-quality claims:

- M1956 selected a bounded 80-source panel from the calibrated source-mining
  pool with the intended source-kind, role, and provenance balance;
- M1958 materialized that panel into 80 executable specs and 960 planned
  workload cells with zero contract, forbidden-key, duplicate-workload, missing
  profile, or guardrail failures;
- M1960 reset-validates the 80 executable specs with `80/80` success and clean
  human-view contract checks;
- M1963 provides a focused measured runner that preserves calibrated repair
  metadata as first-class episode and aggregate fields;
- M1964 freezes a bounded measured execution command and pass gates;
- the branch is ready to run measured execution as public diagnostic data.

Supported process claims:

- the workflow synthesis guard correctly prevented an 11th non-synthesis
  milestone in the same branch;
- the branch separated selection, no-reset materialization, reset validation,
  runner implementation, command design, and measured execution;
- no private holdout, controller-specific tuning, actor input change, training,
  replay, PPO, or ranking was used.

## Falsified Or Unsupported Claims

Falsified in this branch:

```text
The old generic M1928 preflight is an exact schema match for calibrated
M1956/M1958 materialization.
```

Reason: M1957 found that the older preflight route was tied to older source
schemas and would not preserve the calibrated repair-wave selected-source
metadata exactly.

Falsified in this branch:

```text
The legacy M1936 measured runner can be used directly for calibrated measured
execution without a focused adapter.
```

Reason: M1962 found that the legacy runner could reuse rollout primitives but
did not preserve repair source kind, quota, role semantics, normalized surface,
base geometry, and representative cell rule as first-class evidence fields.

Still unsupported:

- measured rollout success for the calibrated 960-cell panel;
- controller-family ranking;
- paper-level benchmark evidence;
- policy improvement;
- finite-window vs GRU conclusion;
- level3 self-identification;
- high-fidelity validation readiness.

## Failure Taxonomy Summary

No runtime failure occurred in M1955-M1964. The branch primarily encountered
process/schema blockers:

```text
M1957: schema route mismatch; generic preflight not exact for calibrated sources
M1962: output schema mismatch; legacy measured runner not metadata-preserving
```

These did not weaken the task-quality criteria. They were resolved by focused
adapters and command design while measured execution remained blocked.

Not observed in this branch:

```text
contract_violation
metric_artifact
private_holdout_contamination
training_instability
proof_washout
behavior_regression
controller ranking evidence
level3 self-ID evidence
```

## Public Gate Overfit Risk

Current risk: `medium`.

Risk reducers:

- source selection preserves source-kind, role, and surface diversity;
- calibrated anchors are split `16/16` across post-friction-step and steady
  surfaces rather than selecting a single source family;
- the panel retains stable AEB, stable AES-only, drift-required recovery, and
  unavoidable mitigation roles;
- actor-input guardrails remain clean through materialization and reset;
- profile-specific tuning and ranking-admissible-by-default flags are `0`;
- measured execution is not interpreted until a later result audit.

Remaining risks:

- all artifacts are still public diagnostic evidence;
- M1960 proves reset validity, not rollout outcome quality;
- the calibrated panel is intentionally bounded and may not represent the full
  active-safety scenario distribution;
- M1966 can still produce low-support or offtrack-dominated measured outcomes;
- controller-family ranking remains blocked until measured outcomes are audited
  and comparison-readiness is established.

## Next Branch Decision

Decision:

```text
continue
```

Next milestone:

```text
m1966-executable-v2-task-quality-calibrated-measured-execution
```

M1966 should run only the calibrated measured execution command recorded above.
It must preserve failure rows if any row fails, must not repair or rerun inside
the same milestone, and must not claim ranking, paper-level evidence, policy
improvement, or level3 self-identification. Interpretation belongs to the
subsequent result audit.
