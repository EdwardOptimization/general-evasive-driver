# M1851 Executable V2 Support-First Source Mining Design

- status: completed
- decision: `support_first_source_mining_design_admit_implementation`
- branch: `paper_route_executable_v2_support_first_source_mining`
- parent audit: `docs/m1850-executable-v2-task-source-metadata-redesign-result-audit.md`
- source mining run: `false`
- materialized executable-v2 rows generated: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1849/M1850 proved that the current stable AES-only sources are unsupported:
two sources, twenty-four profiles, zero accepted AES cells, and both sources
blocked from materialization. M1851 designs the next step: mine candidate task
sources by support evidence before any executable-v2 row materialization.

The source miner is a task-quality tool, not a controller comparison. It should
answer:

```text
Which candidate source/role/profile combinations have reset-time support under
the existing scenario classifier and role contract?
```

It must not answer:

```text
Which controller is best?
Can the policy execute the task?
Is this paper-level evidence?
Does this prove self-identification?
```

## Pipeline

The revised executable-v2 pipeline is:

```text
role-aware candidate source templates
  -> no-reset support-first source mining
  -> support evidence tables
  -> M1846 metadata/admissibility gate
  -> materialization only for supported source-role pairs
  -> reset validation
  -> measured execution only after reset audit
```

The miner must not materialize executable-v2 rows. It only emits support
evidence that a later metadata gate can admit or block.

## Candidate Source Inputs

M1852 should implement a helper that accepts candidate source templates from a
CSV or JSON file. Each candidate row should contain:

```text
candidate_source_id
source_family_id
source_role_semantics
source_required_label
source_allowed_labels
require_aeb_infeasible
profile_name
profile_group
speed_ref
mu
friction_step_enabled
friction_step_at
min_time_after_friction_step
obstacle_distance_min
obstacle_distance_max
obstacle_distance_count
obstacle_half_width_min
obstacle_half_width_max
obstacle_half_width_count
max_threshold_score
profile_control_hash
```

The helper may also accept a seed range or source-family generator config, but
the output must still be concrete candidate rows with fixed profile controls.

## Role Support Criteria

Role support is role-specific. A label from one role cannot certify another
role.

### stable_aes_only

Required support:

```text
label == aes_feasible
reject_reason == accepted
require_aeb_infeasible == true
accepted_cell_count >= min_accepted_cells
```

Cells labeled `drift_required` or `unavoidable` are not stable AES evidence.
They should be routed to their own role families.

### stable_aeb

Required support:

```text
label == aeb_feasible
accepted_cell_count >= min_accepted_cells
require_aeb_infeasible == false
```

AEB support cannot certify AES, drift recovery, or mitigation.

### drift_required_recovery

Required support:

```text
label == drift_required
accepted_cell_count >= min_accepted_cells
recovery_horizon_required == true
```

This role means stable AES is insufficient but drift-level lateral authority is
available by the classifier. It is not a fallback proof for stable AES.

### unavoidable_mitigation

Required support:

```text
label == unavoidable
mitigation_metric_contract_present == true
```

This role is not judged by obstacle pass rate. Later measured execution should
use mitigation metrics such as collision speed reduction, heading/yaw control,
road-boundary retention, and post-impact stability, but M1851 does not run those
metrics.

## Extreme-Condition Extension

The design should be compatible with later hidden-condition source families
such as local friction loss, wheel/tire failure, brake loss, steering lag, or
drive loss. These must remain source metadata and simulator/task parameters;
they must not enter actor inputs.

M1852 should not introduce new dynamics faults yet. If a future branch adds
them, it should extend the role contract with explicit support criteria instead
of treating them as stable AES evidence by default.

## Required Outputs

M1852 should implement a no-reset helper that writes:

```text
summary.json
support_first_source_candidates.csv
support_first_profile_support.csv
support_first_accepted_cells.csv
support_first_blocked_candidates.csv
support_first_role_summary.csv
support_first_materialization_admissibility_input.csv
support_first_claim_boundary.csv
```

`support_first_materialization_admissibility_input.csv` must be compatible with
the M1847 metadata helper. It should carry:

```text
support_contract_id
candidate_source_id
source_v1_bounded_panel_spec_id
source_scenario_spec_id
source_role_semantics
source_required_label
source_allowed_labels
source_support_status
source_support_evidence_artifact
source_support_evidence_stage
source_support_profile_count
source_support_feasible_profile_count
source_support_accepted_cell_count_total
source_support_label_counts
source_support_reject_reason_counts
source_support_failure_reason
materialization_admissible
materialization_block_reason
claim_boundary_context
```

The summary should include:

```text
candidate_source_count
candidate_profile_count
role_count
supported_source_count
unsupported_source_count
blocked_candidate_count
accepted_cell_count_total
stable_aes_supported_source_count
stable_aeb_supported_source_count
drift_required_supported_source_count
unavoidable_supported_source_count
labels_enter_actor_input_count
materialized_row_count
guardrail_violation_count
```

## Diversity Requirements

A supported source corpus should not be dominated by one narrow source family.
The helper should report, not enforce in M1852:

```text
source_family_count
profile_group_count
role_count
speed_bucket_count
mu_bucket_count
friction_step_bucket_count
distance_bucket_count
half_width_bucket_count
max_source_family_share
max_profile_group_share
```

Later materialization should require minimum diversity per role before measured
execution or paper-level claims.

## Claim Boundary

M1852 implementation is allowed to claim:

- helper implementation exists;
- focused tests pass;
- source mining execution remains blocked until an execution-design milestone.

M1852 implementation is not allowed to claim:

- support evidence from project artifacts;
- reset success;
- rollout success;
- controller-family ranking;
- paper-level benchmark result;
- level3 self-identification.

## Guardrails

- source mining run: `false`
- project artifact scan: `false`
- materialized executable-v2 rows generated: `false`
- source repair payload generated: `false`
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

## Next Route

M1852 should implement the no-reset source mining helper and focused tests. It
should not execute source mining on project artifacts. The first project-artifact
run must be a separate execution-design milestone with fixed inputs, grid sizes,
expected counts, output directory, and blocked claims.

## Claim Boundary

Supported:

- support-first source mining design;
- role-specific source support criteria;
- M1852 implementation route.

Unsupported:

- source mining results;
- materialized executable-v2 rows;
- reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
