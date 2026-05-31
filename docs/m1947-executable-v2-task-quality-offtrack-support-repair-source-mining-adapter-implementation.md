# M1947 Executable V2 Task-Quality Offtrack Support Repair Source-Mining Adapter Implementation

- status: completed
- decision: `task_quality_offtrack_support_repair_source_mining_incomplete_route_to_result_audit`
- result class: `task_quality_offtrack_support_repair_source_mining_incomplete_or_fail`
- branch: `paper_route_task_quality_offtrack_support_repair`
- implementation: `src/autodrift/executable_v2_task_quality_offtrack_support_repair_source_mining.py`
- focused tests: `2 passed`
- summary: `runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/summary.json`
- reset/rollout/measured execution in M1947: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_offtrack_support_repair_source_mining \
  --repair-templates configs/executable_v2_task_quality_offtrack_support_repair_candidates_v0.json \
  --executable-task-specs runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json \
  --output-dir runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining \
  --next-blocker m1948-executable-v2-task-quality-offtrack-support-repair-source-mining-result-audit
```

Return code:

```text
0
```

## Implementation Result

The adapter executed and wrote all source-mining/preflight artifacts, but the
pre-registered support gate did not pass.

Clean parts:

```text
input_template_count: 160 / 160
source_candidate_count: 160 / 160
resolution_failure_count: 0
accepted_cell_count_total: 1949
supported_source_count: 66
public_gate_supported_source_count: 40
guardrail_violation_count: 0
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

Failed source-kind gate:

```text
anchor_neighborhood_supported_source_count: 0 / required 16
success_stabilizer_supported_source_count: 39 / required 16
offtrack_boundary_relief_supported_source_count: 11 / required 8
mitigation_isolation_check_source_count: 16 / required 16
```

The broad support gates were actually satisfied:

```text
supported_source_count >= 64: true
public_gate_supported_source_count >= 24: true
```

The failure is localized to anchor-neighborhood support.

## Failure Localization

The anchor-neighborhood rows are slice-level stable-AEB anchors. They have no
exact M1928 source id, so the adapter used M1946 fallback geometry.

The source classifier rejected these rows because the fallback geometry
produced `aes_feasible`, while `stable_aeb` requires `aeb_feasible`:

```text
dominant_label: aes_feasible
dominant_reject_reason: label_not_allowed
source_support_failure_reason: label_role_mismatch
accepted_cell_count: 0
```

This is not:

- a code crash;
- a missing artifact;
- a reset or rollout failure;
- a contract violation;
- a ranking/paper/self-ID claim issue.

It is a source-mining design/mapping issue:

```text
slice-level stable-AEB fallback geometry is too hard and maps to AES, not AEB.
```

## Supported Claims

M1947 supports:

- the source-mining adapter implementation exists and passes focused tests;
- all 160 repair templates can be mapped into source candidates;
- no resolution failure occurred;
- no environment interaction or ranking occurred;
- source-mining support exists in success-stabilizer, offtrack-relief, and
  mitigation-isolation groups;
- the anchor-neighborhood fallback geometry must be audited before repair.

## Unsupported Claims

Still unsupported:

- off-track support repair success;
- reset validity;
- measured execution readiness;
- controller-family ranking;
- finite-window vs GRU conclusion;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1948-executable-v2-task-quality-offtrack-support-repair-source-mining-result-audit
```

M1948 should audit whether the right next move is fallback-geometry repair,
anchor template repair, or broader scenario redesign. It should not patch the
thresholds inside the audit.
