# M2409 Paper-Route Current-Sim Dual-Axis Repair-Plan Materialization Branch Synthesis

- status: completed
- synthesis decision: `promote_to_next_branch`
- route decision: `promote_to_source_linked_reset_evidence_branch`
- manifest: `experiments/manifests/m2409-paper-route-current-sim-dual-axis-repair-plan-materialization-branch-synthesis.json`
- parent synthesis: `docs/m2403-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-branch-synthesis.md`
- parent repair-plan summary: `runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/summary.json`
- parent candidate summary: `runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/summary.json`
- parent adapter summary: `runs/m2408_paper_route_current_sim_dual_axis_offtrack_containment_candidate_reset_load_validation_adapter/summary.json`
- rerun/new measured rollout in M2409: `false`
- reset/repair/training/replay/PPO/ranking/winner: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Evidence Summary

M2404-M2408 converted the M2397 offtrack-dominated measured outcome into a
compact, guarded repair-candidate surface, but did not yet create driver
improvement evidence.

Repair-plan materialization:

```text
M2404 result_class: current_sim_dual_axis_bounded_repair_plan_materialization_pass
total repair-plan rows: 1313
offtrack repair-plan rows: 203
collision guardrail rows: 65
R4 mitigation rows: 57
diagnostic monitoring rows: 1048
repair/training/ranking/guardrail violations: 0
```

Candidate materialization:

```text
M2406 result_class: current_sim_dual_axis_offtrack_containment_repair_candidate_materialization_pass
assigned offtrack repair-plan rows: 203/203
candidate overlays: 4/4
candidate overlay outside run dir: 0
guardrail metadata rows: 8
collision/R4 source rows: 65/57
active overwrite/repair/training/ranking/winner/guardrail counts: 0/0/0/0/0/0
```

Candidate families:

```text
c01_geometry_timing_containment: source rows 6, mean offtrack 0.83038
c02_hidden_dynamics_response_containment: source rows 88, mean offtrack 0.87015
c03_general_offtrack_boundary_containment: source rows 82, mean offtrack 0.85687
c04_role_conditioned_containment: source rows 27, mean offtrack 0.87432
```

Adapter validation:

```text
M2408 result_class: current_sim_dual_axis_offtrack_containment_candidate_reset_load_validation_adapter_pass
candidate/overlay load pass: 4/4
schema/table/source-key/outside-run-dir failures: 0/0/0/0
guardrail metadata/claim-boundary failures: 0/0
missing collision/R4 guardrail counts: 0/0
active overwrite/repair/training/ranking/winner/contract/oracle/guardrail counts: 0/0/0/0/0/0/0/0
```

Pre-synthesis source-link check against the M2391 reset-valid effective
candidate surface:

```text
c01_geometry_timing_containment: source keys 6, matched M2391 keys 3, matched effective candidates 3
c02_hidden_dynamics_response_containment: source keys 88, matched M2391 keys 48, matched effective candidates 24
c03_general_offtrack_boundary_containment: source keys 82, matched M2391 keys 30, matched effective candidates 30
c04_role_conditioned_containment: source keys 27, matched M2391 keys 27, matched effective candidates 27
```

This means every compact family has a non-empty link to already reset-valid
effective-candidate scenario specs. It does not mean the M2406 overlay levers
have been executed.

## Supported Claims

Supported:

```text
M2404-M2408 successfully transformed the offtrack-dominated negative measured
panel into a compact four-family repair-candidate surface with collision and R4
guardrails attached.

The four candidate overlays are structurally loadable, run-dir-only, and claim
bounded.

Every candidate family has at least one source-linked path back to M2391
reset-valid effective candidate scenario specs, so a bounded reset-evidence
branch is admissible.
```

This advances workflow and scenario/task-quality evidence. It is not an
engineering-driver improvement, controller-family comparison, self-ID result, or
paper verdict.

## Falsified Claims

Falsified or blocked:

```text
M2406/M2408 candidates are executable repairs:
  blocked because their candidate_levers are audit/containment semantics, not
  active env-config patches or trained policy updates.

M2408 proves reset success:
  blocked because M2408 loaded JSON overlays only; no AutoDriftEnv reset ran.

M2404-M2408 improve the driver:
  blocked because no measured rollout, policy action, replay, PPO, repair
  execution, or training ran.

The branch can continue with another ordinary artifact audit:
  blocked by the local-search guard after six consecutive non-evidence
  milestones.

Current-sim, paper-level, finite-window-vs-GRU, or level3 self-ID verdict:
  blocked because this branch contains no controller comparison, history
  intervention, private holdout, or promotion gate.
```

## Failure Taxonomy Summary

Observed:

```text
driver_outcome_failure:
  offtrack-dominated failure remains inherited from M2397.

local_search_guard_triggered:
  the branch reached six consecutive non-evidence milestones after M2408.

evidence_gap:
  compact repair families are not yet reset-executable or measured.
```

Not observed:

```text
metric_artifact
lineage_invalid
contract_violation
scenario_sampling_failure in M2408
active config overwrite
repair execution
training repair success
candidate/profile/controller ranking
winner selection
hidden/oracle actor-input injection
```

## Public Gate Overfit Risk

Risk level: `medium-high`.

Why:

```text
The branch repeatedly reprocessed the same public M2397/M2399/M2401 artifacts.
Those steps were useful for boundary cleanup and guardrail separation, but they
now risk becoming a gate-passing artifact pipeline instead of producing new
driver evidence.
```

Required mitigation:

```text
Do not create another abstract repair-plan or overlay audit in the same branch.
Move to a new branch that produces reset evidence over concrete env configs, or
stop if concrete source links cannot be materialized.
Do not rank the four families or treat them as winners.
Do not run PPO or repair training before reset/source-link evidence exists.
```

## Actual Progress Versus Process Overhead

Actual capability changed:

```text
Before M2404, the project had a clean negative measured panel and broad
offtrack/collision/R4 target categories.

After M2408, the project has four compact offtrack containment families with
complete source-row coverage for the 203 offtrack repair targets, collision and
R4 guardrail metadata, and read-only adapter validation.
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

It moves the route from broad offtrack diagnosis to compact guarded families,
but it does not move the paper route to a positive current-sim controller result.

## Next Branch Decision

Synthesis decision:

```text
promote_to_next_branch
```

This is a workflow branch promotion, not a checkpoint promotion.

New branch:

```text
paper_route_current_sim_dual_axis_source_linked_reset_evidence
```

Next milestone:

```text
m2410-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-reset-evidence-implementation
```

M2410 should materialize a source-linked reset-evidence panel by joining M2406
candidate-family source keys to M2391 reset-valid effective candidate specs and
then running reset-only validation over the resulting concrete env configs.

Allowed M2410 claims:

```text
source-linked family reset evidence
reset/load compatibility of concrete scenario specs
family coverage and unmatched-key diagnostics
guardrail preservation at the reset-evidence layer
```

Blocked M2410 claims:

```text
repair execution
scenario redesign executed
training repair success
measured driver improvement
candidate ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```

Stop conditions for the new branch:

```text
stop if any candidate family has zero concrete source-linked scenarios
stop if reset validation fails closed
stop if the route requires active config overwrite or actor input changes
stop if family evidence is converted into ranking before measured validation
stop if another five milestones pass without reset or measured evidence
```
