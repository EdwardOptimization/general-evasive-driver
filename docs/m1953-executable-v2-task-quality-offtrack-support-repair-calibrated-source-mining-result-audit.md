# M1953 Executable V2 Task-Quality Offtrack Support Repair Calibrated Source-Mining Result Audit

- status: completed
- decision: `task_quality_calibrated_source_mining_audit_route_to_branch_synthesis`
- audited result class: `task_quality_offtrack_support_repair_source_mining_pass`
- branch: `paper_route_task_quality_offtrack_support_repair`
- audited source: `runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/summary.json`
- reset/rollout/measured execution in M1953: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M1952 applied the M1950 calibrated fallback artifact to the full no-rollout
source-mining adapter. M1953 audits that result and chooses the next route. It
does not rerun source mining, reset environments, execute policies, or rank
controller families.

## M1952 Result

M1952 passed the calibrated source-mining gate:

```text
result_class: task_quality_offtrack_support_repair_source_mining_pass
input_template_count: 160
source_candidate_count: 160
resolution_failure_count: 0
accepted_cell_count_total: 5981
supported_source_count: 130
public_gate_supported_source_count: 40
guardrail_violation_count: 0
```

Source-kind support:

```text
anchor_neighborhood:        64 / 64 supported
success_stabilizer:        39 / 48 supported
offtrack_boundary_relief:  11 / 32 supported
mitigation_isolation_check: 16 / 16 supported
```

Calibrated fallback provenance:

```text
calibrated_anchor_fallback_used_count: 64
calibrated_anchor_fallback_used_by_surface:
  post_friction_step: 32
  steady_surface: 32
```

Guardrails:

```text
environment_reset_started: false
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Comparison To M1947

M1947 failed only because anchor support was zero. M1952 fixes that localized
blocker:

```text
result_class:
  M1947: task_quality_offtrack_support_repair_source_mining_incomplete_or_fail
  M1952: task_quality_offtrack_support_repair_source_mining_pass

accepted_cell_count_total:
  M1947: 1949
  M1952: 5981

supported_source_count:
  M1947: 66
  M1952: 130

public_gate_supported_source_count:
  M1947: 40
  M1952: 40

anchor_neighborhood:
  M1947: 0 / 64
  M1952: 64 / 64

success_stabilizer:
  M1947: 39 / 48
  M1952: 39 / 48

offtrack_boundary_relief:
  M1947: 11 / 32
  M1952: 11 / 32

mitigation_isolation_check:
  M1947: 16 / 16
  M1952: 16 / 16
```

The non-anchor groups did not regress. The improvement is exactly where M1948
localized the failure: stable-AEB anchor fallback geometry.

## Route Decision

The next route is:

```text
m1954-executable-v2-task-quality-offtrack-support-repair-branch-synthesis
```

Reason:

- the source-mining blocker is repaired;
- the branch has reached the workflow synthesis cadence;
- reset/materialized execution should not start until the branch-level evidence
  is synthesized;
- source-mining pass is not itself reset validity or measured controller
  comparison evidence.

M1954 should decide whether to promote to a calibrated reset/materialized
execution branch, continue source repair, pivot, or stop.

## Supported Claims

M1953 supports:

- M1952 is a clean no-rollout calibrated source-mining pass;
- the M1947 anchor blocker is repaired;
- calibrated fallback provenance is explicit and complete;
- the offtrack-support repair branch is ready for synthesis.

## Unsupported Claims

Still unsupported:

- reset validity for the calibrated repaired source set;
- measured execution readiness;
- controller-family ranking;
- finite-window vs GRU conclusion;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1954-executable-v2-task-quality-offtrack-support-repair-branch-synthesis
```
