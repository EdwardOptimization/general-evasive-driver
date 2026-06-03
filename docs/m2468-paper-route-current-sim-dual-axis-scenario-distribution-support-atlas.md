# M2468 Paper-Route Current-Sim Dual-Axis Scenario-Distribution Support Atlas

- status: completed
- result_class: `scenario_distribution_support_atlas_complete`
- manifest: `experiments/manifests/m2468-paper-route-current-sim-dual-axis-scenario-distribution-support-atlas.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_scenario_distribution_support_atlas.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_scenario_distribution_support_atlas.py`
- summary: `runs/m2468_paper_route_current_sim_dual_axis_scenario_distribution_support_atlas/summary.json`
- reset/rollout/policy action/scenario-redesign execution/repair/training/replay/PPO in M2468: `reset_only`
- ranking/winner selection in M2468: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign-executed/training-repair/current-sim verdict claims: `false`

## Source Admission

M2468 admitted the M2455 scenario-quality candidate table, the M2466
seed-fragility panel, and the M2467 pivot audit:

```text
source_admission_failure_count: 0
source_candidate_row_count: 30
atlas_cell_count: 15
candidate_group_coverage_count: 5
fixed_m2464_r1_reuse_count: 0
```

The atlas does not retry or repair the exact fixed M2464 R1 overlay rows. It
builds distribution-level reset-support cells across stable avoidable, stable
AES, handling-limit/drift-required, hidden-dynamics, and unavoidable mitigation
groups.

## Atlas Result

M2468 ran `15` atlas cells with `8` reset seeds per cell:

```text
diagnostic_attempt_count: 120
reset_success_count: 109
reset_failure_count: 11
reset_success_rate: 0.9083333333333333
support_class_counts: {'reset_support_full': 11, 'reset_support_partial': 4}
atlas_classification: distribution_support_atlas|seed_fragility
guardrail_violation_count: 0
environment_step_count: 0
policy_action_executed: false
environment_rollout_started: false
repair_execution_started: false
training_started: false
ranking_admissible_count: 0
winner_selected_count: 0
```

Group support:

```text
stable_feasibility_support: 24/24 reset success, full support
stable_aes_support: 14/24 reset success, partial support
handling_limit_guardrail: 23/24 reset success, mixed full/partial support
hidden_dynamics_guardrail: 24/24 reset success, full support
mitigation_guardrail: 24/24 reset success, full support
```

Partial-support cells:

```text
stable_aes_broad_threshold_free: 5/8 success
stable_aes_threshold_band: 3/8 success
stable_aes_low_mu_near: 6/8 success
drift_required_nominal: 7/8 success
```

Full-support cells:

```text
stable_avoidable_nominal_center: 8/8
stable_avoidable_lateral_span: 8/8
stable_avoidable_low_mu: 8/8
drift_required_late_boundary: 8/8
drift_required_low_mu: 8/8
hidden_nominal_neighbor: 8/8
hidden_weak_brake: 8/8
hidden_slow_steer: 8/8
unavoidable_close: 8/8
unavoidable_high_speed: 8/8
unavoidable_low_mu: 8/8
```

## Interpretation Boundary

Supported claim:

```text
Distribution-level reset support is broad outside the fixed M2464 R1 rows, but
stable AES remains seed-fragile across the tested broad support bins.
```

Rejected claims:

```text
driver performance improvement
measured actual-success improvement
scenario redesign executed
repair/training success
support-policy/controller/checkpoint/scenario ranking
winner selection
paper-level result
finite-window vs GRU conclusion
level3 self-identification
current-sim verdict
```

M2468 improves scenario/task-quality infrastructure only. It provides broader
reset-readiness evidence that can be audited before any repair design or
measured execution route.

## Decision

M2468 routes to:

```text
m2469-paper-route-current-sim-dual-axis-scenario-distribution-support-atlas-result-audit
```

M2469 must audit whether this atlas supports a bounded stable-AES sampler/support
repair design, a measured-readiness preflight route, or another synthesis step.
It must not execute reset reruns, rollout, policy actions, repair, training,
ranking, winner selection, or verdict claims inside the audit.
