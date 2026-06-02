# M2425 Paper-Route Current-Sim Dual-Axis Source-Linked Repair-Plan Materialization Branch Synthesis

- status: completed
- synthesis decision: `promote_to_next_branch`
- route decision: `promote_to_source_linked_repair_candidate_reset_evidence_branch`
- manifest: `experiments/manifests/m2425-paper-route-current-sim-dual-axis-source-linked-repair-plan-materialization-branch-synthesis.json`
- parent synthesis: `docs/m2419-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-branch-synthesis.md`
- parent repair-plan summary: `runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization/summary.json`
- parent candidate summary: `runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/summary.json`
- parent adapter summary: `runs/m2424_paper_route_current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter/summary.json`
- rerun/new measured rollout in M2425: `false`
- reset/repair/training/replay/PPO/ranking/winner: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Evidence Summary

M2420-M2424 converted the M2413/M2417 source-linked offtrack-dominated outcome
surface into a compact, guarded source-linked repair-candidate surface, but did
not yet create driver improvement evidence.

Repair-plan materialization:

```text
M2420 result_class: current_sim_dual_axis_source_linked_bounded_repair_plan_materialization_pass
repair_plan_row_count: 2844
offtrack_repair_plan_row_count: 59
collision_guardrail_plan_row_count: 30
r4_mitigation_plan_row_count: 43
max_step_noncompletion_plan_row_count: 1
speed_too_low_plan_row_count: 1
diagnostic_monitoring_row_count: 2733
family_membership_diagnostic_row_count: 110
repair/training/ranking/winner/guardrail violations: 0
```

Candidate materialization:

```text
M2422 result_class: current_sim_dual_axis_source_linked_repair_candidate_materialization_pass
assigned offtrack repair-plan rows: 59/59
candidate overlays: 4/4
candidate overlay outside run dir: 0
guardrail metadata rows: 24
collision/R4/max-step/speed-low/diagnostic/family source rows: 30/43/1/1/2733/110
active overwrite/repair/training/ranking/winner/guardrail counts: 0/0/0/0/0/0
```

Candidate families:

```text
c01_source_linked_geometry_timing_containment: source rows 5
c02_source_linked_hidden_dynamics_response_containment: source rows 26
c03_source_linked_role_conditioned_containment: source rows 27
c04_source_linked_outcome_failure_surface_containment: source rows 1
```

Adapter validation:

```text
M2424 result_class: current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter_pass
candidate/overlay load pass: 4/4
schema/table/source-key/outside-run-dir failures: 0/0/0/0
guardrail metadata failures: 0
diagnostic-family metadata failures: 0
claim-boundary failures: 0
missing collision/R4/max-step/speed-low/diagnostic/family guardrail counts: 0/0/0/0/0/0
active overwrite/repair/training/ranking/winner/contract/oracle/guardrail counts: 0/0/0/0/0/0/0/0
```

## Supported Claims

Supported:

```text
M2420-M2424 successfully transformed the source-linked offtrack-dominated
measured panel into four compact source-linked repair-candidate overlays with
collision, R4, max-step, speed-too-low, diagnostic, and family metadata
attached.

The four candidate overlays are structurally loadable, run-dir-only, and claim
bounded.

Diagnostic and family-membership rows remained monitoring-only and were not
converted into family/profile/candidate rankings or winners.

The branch is ready for a new reset-only evidence route over concrete env
configs, if source links can be materialized.
```

This advances workflow and scenario/task-quality readiness. It is not an
engineering-driver improvement, controller-family comparison, self-ID result, or
paper verdict.

## Falsified Claims

Falsified or blocked:

```text
M2422/M2424 candidates are executable repairs:
  blocked because their candidate_levers are audit/containment semantics, not
  active env-config patches or trained policy updates.

M2424 proves reset success:
  blocked because M2424 loaded JSON overlays only; no AutoDriftEnv reset ran.

M2420-M2424 improve the driver:
  blocked because no measured rollout, policy action, replay, PPO, repair
  execution, or training ran.

The branch should continue with another ordinary artifact audit:
  blocked by the local-search guard and the absence of new driver evidence.

Current-sim, paper-level, finite-window-vs-GRU, or level3 self-ID verdict:
  blocked because this branch contains no controller comparison, history
  intervention, private holdout, promotion gate, or measured improvement.
```

## Failure Taxonomy Summary

Observed:

```text
driver_outcome_failure:
  offtrack-dominated failure remains inherited from M2413.

local_search_guard_triggered:
  the branch has produced repair-plan, candidate, audit, and adapter artifacts
  after M2419 and must synthesize before another ordinary artifact step.

evidence_gap:
  compact repair candidates are not yet reset-executable or measured.
```

Not observed:

```text
metric_artifact
lineage_invalid
contract_violation
scenario_sampling_failure in M2424
active config overwrite
repair execution
training repair success
candidate/family/profile/controller ranking
winner selection
hidden/oracle actor-input injection
```

## Public Gate Overfit Risk

Risk level: `medium-high`.

Why:

```text
The branch repeatedly reprocessed the same public source-linked measured and
target-consolidation artifacts. Those steps were useful for boundary cleanup
and guardrail separation, but they now risk becoming a gate-passing artifact
pipeline instead of producing new driver evidence.
```

Required mitigation:

```text
Do not create another abstract repair-plan, overlay, or adapter audit in the
same branch.

Move to a new branch that produces reset-only evidence over concrete env
configs, or stop if concrete source links cannot be materialized.

Do not rank the four families or treat them as winners.

Do not run PPO or repair training before source-linked reset evidence and a
fresh measured-validation design exist.
```

## Actual Progress Versus Process Overhead

Actual capability changed:

```text
Before M2420, the project had source-linked measured validation and compact
target/guardrail categories.

After M2424, the project has four compact source-linked repair candidates with
complete offtrack-row coverage, six-way guardrail metadata, and read-only
adapter validation.
```

Process overhead:

```text
medium-high
```

Reason:

```text
The branch was careful and prevented ranking/verdict shortcuts, but it is now
too deep inside artifact materialization. Another same-branch audit would not
change the scientific evidence.
```

Paper verdict delta:

```text
slightly positive for workflow readiness, neutral for driver capability.
```

It moves the route from bounded repair-plan rows to compact guarded candidate
artifacts, but it does not move the paper route to a positive current-sim
controller result.

## Next Branch Decision

Synthesis decision:

```text
promote_to_next_branch
```

This is a workflow branch promotion, not a checkpoint promotion.

New branch:

```text
paper_route_current_sim_dual_axis_source_linked_repair_candidate_reset_evidence
```

Next milestone:

```text
m2426-paper-route-current-sim-dual-axis-source-linked-repair-candidate-reset-evidence-implementation
```

M2426 should materialize a source-linked reset-evidence panel by joining M2422
candidate source keys to reset-valid effective candidate scenario specs, then
running reset-only validation over the resulting concrete env configs.

Allowed M2426 claims:

```text
source-linked repair-candidate reset evidence
reset/load compatibility of concrete scenario specs
candidate coverage and unmatched-key diagnostics
guardrail preservation at the reset-evidence layer
```

Blocked M2426 claims:

```text
repair execution
scenario redesign executed
training repair success
measured driver improvement
candidate ranking
source-linked family ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```

If M2426 cannot materialize source-linked reset evidence without ranking,
active config overwrite, or hidden/oracle actor inputs, the route should pivot
to artifact repair or scenario-quality reassessment instead of measured rollout.
