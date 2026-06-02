# M2427 Paper-Route Current-Sim Dual-Axis Source-Linked Repair-Candidate Reset Evidence Result Audit

- status: completed
- decision: `matched_subset_reset_evidence_accepted_route_to_measured_reindex_implementation`
- manifest: `experiments/manifests/m2427-paper-route-current-sim-dual-axis-source-linked-repair-candidate-reset-evidence-result-audit.json`
- parent implementation: `docs/m2426-paper-route-current-sim-dual-axis-source-linked-repair-candidate-reset-evidence-implementation.md`
- parent summary: `runs/m2426_paper_route_current_sim_dual_axis_source_linked_repair_candidate_reset_evidence/summary.json`
- rerun/reset/rollout/repair/training/replay/PPO: `false`
- candidate/support/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2427 accepts M2426 as a clean reset-only fail-closed result for the matched
source-linked repair-candidate subset. It rejects any all-four-family measured
validation claim.

Accepted evidence:

```text
result_class: current_sim_dual_axis_source_linked_repair_candidate_reset_evidence_fail_closed
candidate_overlay_load_count: 4
candidate_family_count: 4
matched_family_count: 3
family_without_match_count: 1
fail_closed_unmatched_source_key_result_recorded: true
source_effective_candidate_count: 54
matched_effective_candidate_count: 54
source_linked_scenario_reference_count: 2049
unique_reset_target_count: 350
static_validation_failure_count: 0
environment_reset_attempt_count: 350
environment_reset_success_count: 350
environment_reset_failure_count: 0
environment_step_count: 0
policy_action_executed: false
guardrail_violation_count: 0
```

Matched family coverage:

```text
c01_source_linked_geometry_timing_containment:
  matched effective candidates: 3
  scenario refs: 388
  unique reset targets: 290
  unmatched source keys: 2

c02_source_linked_hidden_dynamics_response_containment:
  matched effective candidates: 24
  scenario refs: 593
  unique reset targets: 280
  unmatched source keys: 2

c03_source_linked_role_conditioned_containment:
  matched effective candidates: 27
  scenario refs: 1068
  unique reset targets: 300
  unmatched source keys: 0
```

Blocked family:

```text
c04_source_linked_outcome_failure_surface_containment:
  matched effective candidates: 0
  scenario refs: 0
  unique reset targets: 0
  unmatched source keys: 1
  blocker: episode_rows:outcome_bucket:off_track_noncollision_noncompletion
```

## Existing Measured-Panel Alignment

M2427 verified that the M2426 reset target set is exactly the same 350-key
denominator already measured in M2413:

```text
M2426 reset targets: 350
M2413 measured reset targets: 350
M2426 not in M2413: 0
M2413 not in M2426: 0
```

Therefore, the next evidence-producing step should not rerun measured
validation. It should reindex the existing M2413 measured rows using the M2426
source-linked repair-candidate family memberships.

## Failure Taxonomy

Observed:

```text
family_source_link_failure:
  one candidate family, c04 outcome-failure-surface containment, has zero
  matched M2391 effective candidates.

unmatched_source_key_diagnostic:
  five source keys are unmatched; c04's outcome_bucket key is the only
  family-blocking key.

driver_outcome_failure:
  offtrack-dominated failure remains inherited from M2413 until reindexing or
  further measured evidence changes it.
```

Not observed:

```text
scenario_sampling_failure
contract_violation
metric_artifact in M2426 reset evidence
active config overwrite
repair execution
training repair success
candidate/profile/controller ranking
winner selection
environment step or policy action in M2426
```

## Route Decision

Decision:

```text
matched_subset_reset_evidence_accepted_route_to_measured_reindex_implementation
```

Next milestone:

```text
m2428-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-implementation
```

M2428 should join:

```text
M2413 episode_rows.csv
M2413 episode_family_membership_rows.csv if needed
M2426 source_linked_family_rows.csv
M2426 source_linked_scenario_rows.csv
M2426 reset_target_rows.csv
```

and produce a non-ranking measured reindex for:

```text
c01_source_linked_geometry_timing_containment
c02_source_linked_hidden_dynamics_response_containment
c03_source_linked_role_conditioned_containment
```

c04 must remain explicitly excluded:

```text
c04_source_linked_outcome_failure_surface_containment excluded because matched_effective_candidate_count = 0
```

## Claim Boundary

Supported:

```text
M2426 is accepted as reset-only evidence for the matched 3-family subset.

The M2426 reset target denominator is exactly aligned with the already measured
M2413 350-reset-target panel.

The next admissible evidence-producing route is measured-result reindexing, not
rerun and not all-four-family measured validation.
```

Blocked:

```text
all-four-family measured validation readiness
c04 outcome-failure-surface measured evidence
new measured rollout
repair execution
scenario redesign executed
training repair success
candidate family ranking
support/controller ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```
