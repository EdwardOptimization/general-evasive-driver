# M2024 Paper-Route Controlled Comparison Panel Preflight Result Audit

- status: completed
- decision: `controlled_comparison_panel_preflight_audit_route_to_source_coverage_repair_design`
- audited summary: `runs/m2023_paper_route_controlled_comparison_panel_preflight/summary.json`
- audited coverage: `runs/m2023_paper_route_controlled_comparison_panel_preflight/source_coverage.csv`
- audited claim boundary: `runs/m2023_paper_route_controlled_comparison_panel_preflight/claim_boundary.csv`
- reset/rollout/measured execution in M2024: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Completeness Audit

M2023 completed the no-rollout preflight:

```text
result_class: controlled_comparison_panel_preflight_source_repair_required
profile_count: 12
task_family_count: 5
panel_source_count: 171
workload_cell_count: 2052
guardrail_violation_count: 0
panel_ready_for_routing_smoke: false
```

M2023 did not execute the environment or actor:

```text
environment_reset_started: false
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
private_holdout_used: false
actor_input_contract_changed: false
```

## Coverage Audit

The preflight is complete as an artifact layer but not ready for routing smoke:

```text
profile_count: true
all_task_families_present: true
min_family_source_count: false
target_family_source_count: false
source_kind_share: false
m1683_guardrail: true
```

Detailed gaps:

```text
T1_reactive_active_safety:
  source_count = 6
  source_kind_count = 1
  max_single_source_kind_share = 1.0000
  blocker = count below 12 and source-kind singleton

T2_same_current_different_older_history:
  source_count = 36
  source_kind_count = 4
  max_single_source_kind_share = 0.5833
  blocker = dominant actuator_delay_proxy+capability_step_proxy source kind

T3_active_diagnostic_warmup:
  source_count = 24
  source_kind_count = 4
  max_single_source_kind_share = 0.3750
  blocker = slightly above max single-source-kind share target 0.35

T4_variable_diagnostic_delay:
  source_count = 33
  source_kind_count = 4
  max_single_source_kind_share = 0.2727
  status = count and source-kind share pass

T5_source_rich_extreme_dynamics:
  source_count = 72
  source_kind_count = 8
  max_single_source_kind_share = 0.2917
  status = count and source-kind share pass
```

This is not a tooling failure. It is a useful scenario/source coverage audit:
the controlled panel can be represented, but the active-safety and history
families need repair before execution.

## Supported Claims

Supported:

```text
M2023 produced clean no-rollout controlled-comparison panel artifacts.
The project now has a concrete 12-profile / 5-family workload representation.
The coverage blocker is localized to T1/T2/T3 source count/diversity.
T4/T5 are currently the only families that pass the registered count/share
thresholds.
```

Unsupported:

```text
The panel is ready for routing smoke.
The panel is ready for controller-family ranking.
The panel supports a finite-window-vs-GRU conclusion.
The panel supports paper-level benchmark evidence.
The panel supports level3 self-identification.
```

## Route Decision

Decision:

```text
route_to_source_coverage_repair_design
```

Rationale:

- Direct routing smoke is blocked because `panel_ready_for_routing_smoke=false`.
- Threshold revision is not justified yet. The failed thresholds encode the
  source-rich and anti-overfit requirements from M2022.
- Split-panel T4/T5 routing smoke would test plumbing on the ready subset, but
  it would fragment the paper route before the active-safety and warmup/history
  families are repaired.
- The repair target is concrete: top up or rebalance T1/T2/T3 while preserving
  the T4/T5 coverage that already passes.

Failure taxonomy:

```text
scenario_sampling_failure:
  T1 has too few active-safety sources and is source-kind singleton.

objective_overfit risk:
  running only ready T4/T5 would bias the next route toward the families that
  already pass public coverage, leaving active-safety coverage unresolved.
```

Rejected routes:

```text
direct_routing_smoke:
  rejected because panel_ready_for_routing_smoke is false.

threshold_revision:
  rejected until an audit proves the thresholds are mismatched rather than
  exposing real source imbalance.

split_T4_T5_smoke:
  rejected for now because the full panel blocker is localized and repairable.

branch_stop:
  rejected because the preflight produced clean artifacts and a concrete repair
  target.

branch_synthesis_now:
  rejected because the branch has not repeated the same failure three times and
  the next evidence increment is source repair, not another narrow public-row
  tweak.
```

## M2025 Requirements

M2025 should design a no-rollout source-coverage repair for the controlled
comparison panel.

Repair targets:

```text
T1_reactive_active_safety:
  raise clean source count from 6 to at least 12;
  reduce source-kind singleton dominance below 0.35 if enough source kinds
  exist in prior task-quality artifacts;
  preserve stable AEB, stable AES, drift-required, and unavoidable roles.

T2_same_current_different_older_history:
  rebalance or top up so max single-source-kind share <= 0.35.

T3_active_diagnostic_warmup:
  rebalance or top up so max single-source-kind share <= 0.35.

T4/T5:
  preserve existing passing coverage unless the repair requires deduplication
  that is explicitly audited.
```

M2025 must not run environment rollout, train, replay, rank controller families,
or claim finite-window-vs-GRU/self-ID evidence.
