# M1797 Executable V2 Label-Source Compatibility Repair Design

- status: completed
- decision: `label_source_compatibility_repair_design_admit_preflight_implementation`
- source synthesis: `docs/m1796-paper-route-role-specific-panel-metric-repair-branch-synthesis.md`
- reset run: `false`
- rollout started: `false`
- training/replay/PPO: `false`

## Problem

M1794/M1795 showed that M1790's executable v2 specs are schema-clean but not
fully reset-feasible:

```text
attempted specs: 312
reset successes: 272
sampling failures: 40
```

The dominant failure is not adapter metadata loss. It is source-label
compatibility:

- `m1771-bp1-00` supports `aeb_feasible` under M1794 but fails
  `aes_feasible` across all `12` profiles.
- `m1771-bp1-02` supports `aeb_feasible` under M1794 but fails
  `aes_feasible` across all `12` profiles.
- `m1771-bp1-05` supports `aes_feasible` under M1794 but fails
  `aeb_feasible` across all `12` profiles.

The remaining `4` failures are sparse hidden-robust AES cells inside otherwise
mostly successful source-label groups. They should not be mixed with the
systematic stable failure class.

## Design Goal

Define a no-reset compatibility repair preflight that turns M1794 evidence into
a durable source-label contract before any new reset, rollout, measured
execution, or ranking.

The repair must:

- preserve all `12` profile controls;
- keep actor inputs unchanged and label-free;
- keep ranking blocked by default;
- avoid profile-specific tuning;
- quarantine unsupported source-label pairs instead of forcing them into the
  executable panel;
- separate systematic source-label incompatibility from sparse seed/profile
  fragility.

## Source-Label Support Contract

Group rows by:

```text
source_label_group_id =
  source_scenario_spec_id
  + v2_role_surface_id
  + v2_task_label
  + hidden_dynamics_bucket
  + road_boundary_bucket
  + obstacle_timing_bucket
  + obstacle_lateral_bucket
```

For each group, compute:

```text
profile_count
reset_success_count
sampling_failure_count
success_profile_names
failure_profile_names
support_status
systematic_failure
sparse_failure
replacement_required
compatible_for_reset_rerun
ranking_admissible_by_default
labels_enter_actor_input
```

Support status values:

| status | meaning |
| --- | --- |
| `supported_observed` | all observed profile cells reset successfully |
| `unsupported_systematic` | all observed profile cells fail sampling |
| `sparse_fragile` | both success and sampling failure exist in the group |
| `unobserved` | source-label group exists in metadata but has no M1794 evidence |

Only `supported_observed` groups are allowed into the immediate compatible
reset-rerun spec set. `unsupported_systematic` groups become compatibility
violations. `sparse_fragile` groups are quarantined for a later seed-fragility
or tight-filter probe.

## Artifacts

M1798 implementation should write:

```text
summary.json
source_label_support.csv
compatibility_violation_rows.csv
sparse_failure_rows.csv
compatible_executable_v2_panel_specs.json
compatible_executable_v2_panel_specs.csv
compatible_executable_v2_panel_matrix.csv
replacement_need_rows.csv
claim_boundary.csv
```

Required summary fields:

```text
input_spec_count
input_reset_row_count
compatible_spec_count
compatibility_violation_count
sparse_failure_count
replacement_need_count
profile_control_count
role_surface_count
labels_enter_actor_input_count
ranking_admissible_by_default_count
guardrail_violation_count
compatible_reset_rerun_admissible
measured_execution_admissible
controller_family_ranking_admissible
```

Expected from current M1794 evidence:

```text
input_spec_count: 312
input_reset_row_count: 312
compatible_spec_count: 272
compatibility_violation_count: 36
sparse_failure_count: 4
replacement_need_count: >0
compatible_reset_rerun_admissible: true
measured_execution_admissible: false
controller_family_ranking_admissible: false
```

The compatible set can be used for a later reset-only rerun, but not for
controller ranking because systematic replacements are still needed to restore
role/label balance.

## Deterministic Repair Rules

Rules for M1798:

1. Read M1790 `executable_v2_panel_specs.json` and M1794 `reset_stress_rows.csv`.
2. Preserve row order by `v2_panel_spec_id`.
3. Mark each row as:
   - `compatible_for_reset_rerun=true` only if its group is
     `supported_observed`;
   - `compatibility_violation=true` if its group is `unsupported_systematic`;
   - `sparse_failure=true` if its group is `sparse_fragile`.
4. Write all unsupported rows to violation or sparse artifacts with the original
   v2 metadata.
5. Do not alter `env_config`, actor input fields, reward, dynamics, or
   termination behavior.
6. Do not tune profile-specific seeds or profile configs.
7. Preserve all twelve profile controls in the support tables, even when a group
   is quarantined.
8. Set all ranking and measured-execution admission flags to false while any
   replacement is required.

## Replacement Need Rules

`replacement_need_rows.csv` should summarize what is missing after quarantine:

```text
v2_role_surface_id
v2_task_label
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
missing_profile_count
reason
recommended_next_action
```

For systematic stable failures, recommended action is:

```text
find_or_materialize_alternate_source_with_observed_label_support
```

For sparse hidden-robust AES failures, recommended action is:

```text
run_seed_fragility_or_tight_filter_probe_after_systematic_repair
```

This distinction prevents the project from overfitting four sparse cells before
repairing the main source-label contract.

## Acceptance Rules

M1798 implementation should pass if:

- focused tests cover supported, unsupported systematic, and sparse fragile
  groups;
- outputs preserve v2 metadata and all `12` profile controls;
- expected current M1794 counts are produced by tests or execution design;
- labels do not enter actor input;
- ranking and measured execution remain blocked;
- no reset, rollout, training, replay, PPO, private holdout, profile tuning,
  actor-input change, or paper-level claim is made.

## Route Decision

Route to:

```text
m1798-executable-v2-label-source-compatibility-preflight-implementation
```

M1798 should implement the preflight helper and focused tests only. A later
execution milestone can run it on M1790/M1794 artifacts and decide whether a
compatible reset-rerun subset is ready or whether source top-up materialization
is required first.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
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

- source-label compatibility repair design;
- separation of systematic stable failures from sparse hidden-robust failures;
- no-reset implementation route.

Unsupported:

- repaired executable panel pass;
- reset rerun result;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
