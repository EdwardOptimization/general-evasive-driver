# M2046 Paper-Route Controlled Routing Smoke Task-Quality Repair Template Result Audit

- status: completed
- decision: `controlled_routing_smoke_task_quality_repair_template_audit_admit_source_mining_design`
- audited artifact: `configs/paper_route_controlled_routing_smoke_task_quality_repair_candidates_v0.json`
- reset/rollout/measured execution in M2046: `false`
- policy actions executed in M2046: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Artifact Audit

M2045 produced a clean no-rollout repair-template artifact:

```text
result_class: controlled_routing_smoke_task_quality_repair_templates_pass
candidate_source_count: 192
expected_candidate_source_count: 192
quota_pass: true
guardrail_violation_count: 0
generated_proxy_paper_claim_count: 0
profile_specific_tuning_count: 0
```

Repair-axis quotas:

```text
l2_offtrack_relief: 64
family_offtrack_relief: 48
zero_success_source_kind_relief: 40
success_neighborhood_expansion: 24
generated_proxy_support_check: 16
```

Split quotas:

```text
public_debug: 112
public_gate: 80
```

Forbidden true counts:

```text
labels_enter_actor_input: 0
profile_specific_tuning: 0
controller_family_ranking_claim_made: 0
finite_window_vs_gru_conclusion_made: 0
paper_level_claim_made: 0
level3_self_id_claim_made: 0
```

## Supported Claims

Supported:

```text
The M2045 repair-template artifact is quota-complete.
The artifact is no-rollout and guardrail-clean.
Generated proxy candidates remain smoke_proxy / paper_validity_claim=false.
The artifact is admissible for a source-mining or materialization design step.
```

Unsupported:

```text
reset validity;
rollout validity;
measured execution success;
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark result;
level3 self-identification.
```

## Route Decision

Selected:

```text
route_to_controlled_routing_smoke_task_quality_repair_source_mining_design
```

M2047 should design the no-rollout conversion from repair templates to concrete
repair source candidates/executable task specs. The design must specify how to:

```text
resolve each parent task source against M2033 executable specs or M2042
localization rows;
apply template deltas to env_config without touching controller profiles;
preserve smoke_proxy and paper_validity_claim=false for generated rows;
preserve public_debug/public_gate split and repair-axis quotas;
fail closed on unresolved parent references or forbidden claim flags.
```

Rejected:

```text
direct reset validation:
  rejected because templates are not executable task specs yet.

direct measured execution:
  rejected because source mining/materialization has not happened.

ranking or candidate qualification:
  rejected because there is no reset/rollout evidence for the repaired panel.

another template tweak:
  rejected because current template artifact passes registered gates.
```

Controller ranking, finite-window-vs-GRU, paper-level comparison, and level3
self-ID claims remain blocked.
