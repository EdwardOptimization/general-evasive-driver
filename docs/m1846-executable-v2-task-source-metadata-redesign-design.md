# M1846 Executable V2 Task-Source Metadata Redesign Design

- status: completed
- decision: `task_source_metadata_redesign_design_admit_implementation`
- branch: `paper_route_executable_v2_task_source_metadata_redesign`
- parent synthesis: `docs/m1845-paper-route-executable-v2-reset-time-aes-feasibility-branch-synthesis.md`
- project artifact scan run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1845 closed the current stable AES-only source-repair route. The problem was
not actor input, policy architecture, or reset mechanics. The immediate problem
was task-source metadata: executable-v2 materialized stable AES rows before
proving that the selected source/reset-speed conditions actually had stable
AES-only support.

M1846 designs a support-first task-source metadata contract. The goal is to make
unsupported rows fail before materialization, not after reset preflight.

## Contract Version

```text
contract_id: executable_v2_support_first_task_source_v1
```

The contract is metadata-only. It must not enter actor inputs and must not
change reward, dynamics, termination behavior, profile controls, or policy
architecture.

## Support-First Pipeline

The new executable-v2 source pipeline should be:

```text
candidate source metadata
  -> source-role support preflight
  -> support evidence artifact
  -> materialization admissibility decision
  -> executable-v2 row materialization
  -> reset validation
  -> measured execution only after reset audit
```

The previous failing order was:

```text
materialization
  -> reset failure
  -> source repair
  -> support scan
```

M1846 replaces that with support-first admission.

## Source Role Separation

Do not force one obstacle role into another.

### stable_aes_only

Required labels:

```text
aes_feasible
```

Support condition:

```text
label == aes_feasible
reject_reason == accepted
require_aeb_infeasible == true
```

Cells labeled `drift_required` or `unavoidable` are not fallback evidence for
stable AES. They must route to their own role families.

### stable_aeb

Required labels:

```text
aeb_feasible
```

Support condition:

```text
label == aeb_feasible
```

AEB rows can be reset-supported by AEB-feasible cells, but they cannot be used
to certify AES.

### drift_required_recovery

Required labels:

```text
drift_required
```

Support condition:

```text
label == drift_required
recovery_horizon_required == true
```

This role is not a failure of stable AES. It is a separate handling-limit task.

### unavoidable_mitigation

Required labels:

```text
unavoidable
```

Support condition:

```text
label == unavoidable
mitigation_metric_contract_present == true
```

Obstacle pass rate is not a primary metric for mitigation.

## Required Metadata Fields

Each candidate source and materialized row should carry these fields:

```text
support_contract_id
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

Allowed `source_support_status` values:

```text
supported
unsupported
unknown
invalid
```

Allowed `source_support_failure_reason` values:

```text
none
no_accepted_cells
label_role_mismatch
threshold_filter_only
friction_timing_filter_only
missing_support_artifact
metadata_join_incomplete
claim_boundary_context_invalid
```

## Materialization Rules

Rules:

1. A source with `source_support_status != supported` is not materialization
   admissible for that role.
2. `stable_aes_only` requires accepted `aes_feasible` support. It cannot use
   `drift_required` or `unavoidable` cells as support.
3. `drift_required_recovery` requires drift-specific role metadata and recovery
   horizon fields.
4. `unavoidable_mitigation` requires mitigation metrics and cannot claim
   obstacle-pass success as the primary metric.
5. `labels_enter_actor_input` must remain `false`.
6. `v2_ranking_admissible_by_default` must remain `false`.
7. Profile controls must be preserved and reported, not tuned per source.

## Context-Aware Claim Boundary

Claim-boundary output must include:

```text
claim_context
claim
admissible
reason
```

Allowed `claim_context` values:

```text
implementation_only
project_artifact_execution
result_audit
branch_synthesis
```

Example:

```text
implementation_only,project_artifact_scan_result,false
project_artifact_execution,project_artifact_scan_result,true
result_audit,source_repair_success,false
branch_synthesis,next_branch_decision,true
```

This prevents the M1843 artifact class where implementation-only wording was
reused during project-artifact execution.

## Required Helper Outputs For M1847

M1847 should implement a no-reset helper that can write:

```text
summary.json
task_source_support_contract.csv
task_source_role_contract.csv
task_source_materialization_admissibility.csv
task_source_blocked_sources.csv
task_source_claim_boundary.csv
```

The helper should accept support evidence tables such as M1843 profile/source
summaries and convert them into materialization admissibility decisions.

Minimum summary fields:

```text
contract_id
input_source_count
input_profile_count
supported_source_count
unsupported_source_count
unknown_source_count
materialization_admissible_source_count
materialization_blocked_source_count
labels_enter_actor_input_count
ranking_admissible_by_default_count
claim_boundary_context_count
guardrail_violation_count
environment_reset_started
environment_rollout_started
policy_action_executed
measured_rollout_started
training_started
replay_started
ppo_used
promoted
private_holdout_used
actor_input_contract_changed
profile_specific_tuning
controller_family_ranking_claim_made
paper_level_claim_made
level3_self_id_claim_made
```

## Focused Tests For M1847

M1847 should add focused tests for:

1. stable AES materialization is blocked when support evidence has zero accepted
   `aes_feasible` cells;
2. drift-required evidence does not certify stable AES;
3. supported stable AES evidence admits materialization while keeping labels out
   of actor input and ranking blocked;
4. missing support evidence yields `unknown` and blocks materialization;
5. claim-boundary rows are context-aware for implementation, execution, audit,
   and synthesis contexts.

## Implementation Route

Route to:

```text
m1847-executable-v2-task-source-metadata-redesign-implementation
```

M1847 should implement the helper and focused tests only. It should not run a
project artifact execution over M1843 yet.

## Guardrails

- project artifact scan run: `false`
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

## Claim Boundary

Supported:

- support-first task/source metadata contract design;
- role separation between stable AES, AEB, drift-required, and mitigation;
- M1847 helper implementation is admitted.

Unsupported:

- metadata redesign implementation;
- project artifact execution;
- source repair success;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
