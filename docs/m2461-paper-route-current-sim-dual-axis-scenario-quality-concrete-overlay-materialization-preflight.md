# M2461 Paper-Route Current-Sim Dual-Axis Scenario-Quality Concrete Overlay Materialization Preflight

- status: completed
- result_class: `scenario_quality_concrete_overlay_materialization_preflight_pass`
- manifest: `experiments/manifests/m2461-paper-route-current-sim-dual-axis-scenario-quality-concrete-overlay-materialization-preflight.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight.py`
- summary: `runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight/summary.json`
- concrete overlays: `runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight/concrete_overlay_rows.csv`
- overlay-augmented candidates: `runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight/candidate_rows_with_overlays.csv`
- adapter summary: `runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight/adapter_summary.json`
- reset/rollout/policy action/scenario-redesign execution/repair/training/replay/PPO: `false`
- ranking/winner selection: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign-executed/training-repair/current-sim verdict claims: `false`

## Result

M2461 materialized the M2460 concrete overlay design and reran the M2458 adapter
over the overlay-augmented candidate table.

```text
result_class: scenario_quality_concrete_overlay_materialization_preflight_pass
source_candidate_row_count: 30
source_preflight_work_item_count: 30
target_preflight_row_count: 6
concrete_overlay_row_count: 6
candidate_rows_with_overlay_count: 6
materialization_error_count: 0
guardrail_violation_count: 0
```

Overlay families:

```text
R0_stable_avoidable: 3
R1_aeb_infeasible_stable_aes: 3
```

Adapter preflight result:

```text
adapter_result_class: scenario_quality_redesign_reset_static_preflight_adapter_static_pass_reset_blocked
adapter_concrete_overlay_available_count: 6
adapter_static_check_fail_count: 0
adapter_guardrail_violation_count: 0
adapter_reset_required_count: 6
adapter_reset_attempted_count: 0
adapter_reset_success_count: 0
adapter_reset_blocked_missing_concrete_overlay_count: 0
```

## Interpretation

M2461 resolves the M2458 missing-overlay readiness blocker for the stable/AES
support rows:

```text
reset_blocked_missing_concrete_overlay_count: 6 -> 0
concrete_overlay_available_count: 0 -> 6
```

This is still preflight evidence only. The adapter deliberately keeps reset
execution disabled and records each concrete-overlay reset row as:

```text
reset_execution_not_enabled_in_m2458_adapter
```

That means M2461 proves the overlay rows are materialized and statically
admissible. It does not prove reset success, rollout success, driver
performance, scenario redesign execution, training repair, paper-level
evidence, finite-window-vs-GRU evidence, level3 self-ID, or a current-sim
verdict.

## Guardrails

The claim boundary remains clean:

```text
labels_enter_actor_input_count: 0
actor_input_contract_changed_count: 0
scenario_redesign_executed: false
environment_reset_started: false
environment_rollout_started: false
measured_policy_rollout_started: false
policy_action_executed: false
repair_execution_started: false
training_started: false
ranking_admissible_count: 0
winner_selected_count: 0
paper_level_claim_made: false
current_sim_verdict_claim_made: false
```

The only failure type still recorded is `scenario_sampling_failure`, inherited
from the adapter's fail-closed reset-disabled rows. In M2461 this is not a
materialization failure because `guardrail_violation_count` is `0`; it is the
expected boundary that reset validation requires a later audit route.

## Decision

Accepted next route:

```text
m2462-paper-route-current-sim-dual-axis-scenario-quality-discriminant-branch-synthesis
```

M2462 must synthesize the M2452-M2461 scenario-quality discriminant branch
before any reset validation route. M2461 resolved the missing-overlay readiness
blocker at preflight level, but the branch has reached workflow synthesis
cadence; the next step is a process synthesis that decides whether bounded
reset-validation design is admissible, whether to pivot, or whether to stop. It
must not execute reset, rollout, policy actions, scenario redesign, repair,
training, ranking, winner selection, or verdict claims.
