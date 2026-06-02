# M2348 Paper-Route Current-Sim Dual-Axis Redesign Calibration Materialization Result Audit

- status: completed
- result_class: `dual_axis_redesign_calibration_materialization_result_accepted_route_to_candidate_config_design`
- manifest: `experiments/manifests/m2348-paper-route-current-sim-dual-axis-redesign-calibration-materialization-result-audit.json`
- parent implementation: `docs/m2347-paper-route-current-sim-dual-axis-redesign-calibration-materialization-implementation.md`
- parent summary: `runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/summary.json`
- reset/rollout/policy action in M2348: `false`
- measured execution in M2348: `false`
- training/replay/PPO in M2348: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`

## Artifact Completeness

M2347 is accepted as a complete artifact-only materialization:

```text
result_class: current_sim_dual_axis_redesign_calibration_materialization_pass
input_redesign_row_count: 26
geometry_timing_input_row_count: 13
hidden_range_input_row_count: 13
secondary_coverage_input_row_count: 9
secondary_coverage_tracked_count: 9
rows_without_candidate_count: 0
actor_contract_violation_count: 0
inactive_secondary_violation_count: 0
guardrail_violation_count: 0
```

The candidate artifacts exist:

```text
calibration_candidate_rows.csv
geometry_timing_candidate_rows.csv
hidden_range_candidate_rows.csv
combined_axis_candidate_rows.csv
secondary_coverage_rows.csv
calibration_config_candidates.json
claim_boundary.csv
summary.json
```

## Candidate Shape Audit

M2347 produces a bounded candidate set:

```text
calibration_candidate_count: 53
geometry_timing_candidate_count: 28
hidden_range_candidate_count: 13
combined_axis_candidate_count: 12
```

This is usable as a candidate source, but it is not yet an executable scenario
pack. Directly validating all candidate rows or all combinations would create a
new local-search/ranking problem. The next step should therefore materialize a
small deterministic config-pack family before any reset or measured validation.

The audit accepts the candidate schema with one caveat:

```text
candidates are metadata patch plans, not executed scenario specs
```

That caveat blocks direct validation reruns until a candidate-config
materialization design defines how to collapse the 53 candidates into bounded
G/H/GH config packs.

## Claim Boundary Audit

M2347 correctly allows only:

```text
artifact_only_dual_axis_calibration_materialization
```

and blocks:

```text
scenario_redesign_executed;
support_policy_ranking;
controller_family_ranking;
paper_level_evidence;
level3_self_identification.
```

M2348 does not change that boundary.

## Decision

M2348 accepts M2347 and routes to candidate config materialization design:

```text
decision: route_to_dual_axis_calibration_candidate_config_materialization_design
next: m2349-paper-route-current-sim-dual-axis-calibration-candidate-config-materialization-design
```

M2349 should design a bounded artifact-only route that converts the candidate
rows into a small set of config packs, for example:

```text
G_primary_pack:
  one deterministic primary G candidate for geometry/timing rows

H_primary_pack:
  one deterministic primary H candidate for hidden-range rows

GH_minimal_pack:
  primary G/H candidates plus GH candidates only where M2347 marks both axes

baseline_reference_pack:
  read-only reference to the current active config, not a modified pack
```

M2349 must not run reset, rollout, measured execution, replay, PPO, controller
comparison, or ranking. It should only design the materializer contract.

## Blocked Claims

Blocked:

```text
scenario redesign executed;
controller comparison ready;
support policies ranked;
controller families ranked;
winner selected;
residual support solved;
paper-level evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Follow-Up Manifest

```text
experiments/manifests/m2349-paper-route-current-sim-dual-axis-calibration-candidate-config-materialization-design.json
```
