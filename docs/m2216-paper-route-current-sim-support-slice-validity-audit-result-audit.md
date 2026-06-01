# M2216 Paper-Route Current-Sim Support-Slice Validity Audit Result Audit

- status: completed
- decision: `current_sim_support_slice_validity_result_audit_route_to_bounded_diagnostic_comparison_design`
- manifest: `experiments/manifests/m2216-paper-route-current-sim-support-slice-validity-audit-result-audit.json`
- audited result: `runs/m2215_paper_route_current_sim_support_slice_validity_audit/summary.json`
- reset in M2216: `false`
- measured execution in M2216: `false`
- policy action executed in M2216: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Checks

M2215 passed the no-rerun validity audit:

```text
result_class: current_sim_support_slice_validity_audit_pass
input_group_count: 212
episode_row_count: 2304
guardrail_violation_count: 0
ranking_admissible_count: 0
```

Validity counts:

```text
scene_backed_candidate: 9
history_family_diagnostic: 13
profile_only_candidate: 18
global_or_scene_blocker: 7
low_sample_or_unresolved: 60
invalid_for_ranking: 105
denominator_imbalanced: 0
```

This is enough to justify a bounded diagnostic comparison design, but not enough
to rank controller families.

## What The Scene-Backed Candidates Mean

The scene-backed candidates are not winner evidence. They are the only
diagnostic slices that are not explicitly profile-axis or history-axis rows:

```text
T1 reactive emergency avoidance: 63 / 192 success
T2 delayed actuator response: 62 / 240 success
T3 diagnostic warmup obstacle reveal: 105 / 528 success
t4_actuator_delay_response: 62 / 240 success
t4_staged_warmup_capability: 105 / 528 success
t5_boundary_axis_retarget: 63 / 192 success
delayed_actuator_response: 62 / 240 success
diagnostic_warmup: 105 / 528 success
reactive_current_response: 63 / 192 success
```

These slices have multi-profile and multi-history denominators, but their
support label is only `candidate_support`, and the global panel is still
offtrack dominated.

## What The Profile/History Candidates Mean

The strongest support is concentrated in explicit finite-window and L2 profile
rows:

```text
history_family_diagnostic: 13
profile_only_candidate: 18
ranking_admissible_count: 0
```

This may be useful for diagnosing why L2 finite windows work better on this
public panel, but it is not a finite-window vs GRU verdict. The result must be
treated as public diagnostic evidence because the panel was created through
multiple public offtrack-support repairs.

## Failure Taxonomy

```text
scenario_sampling_failure:
  The broad panel remains offtrack dominated and not ranking-ready.

none:
  M2215 itself passed; the validity audit did not run environment or policy code
  and did not create a claim violation.
```

## Decision

Selected next route:

```text
m2217-paper-route-current-sim-bounded-diagnostic-comparison-design
```

The next milestone should design a bounded diagnostic comparison over the
scene-backed candidates only. It must:

```text
1. use only M2209/M2212/M2215 artifacts unless a later manifest explicitly
   admits a rerun;
2. keep ranking, winner selection, paper claims, finite-window vs GRU verdicts,
   and self-ID claims blocked;
3. report profile/history outcomes as diagnostic tables, not promotion gates;
4. state when the diagnostic result should route to task-quality repair,
   profile-training audit, or stop.
```

Rejected routes:

```text
direct controller-family ranking from M2215;
direct finite-window vs GRU conclusion;
direct high-fidelity migration;
another blind offtrack-support repair before diagnostic comparison design;
self-ID claim from aggregate support slices.
```

## Claim Boundary

Allowed claim:

```text
M2215 validity artifacts justify a bounded public diagnostic comparison design
over scene-backed candidate slices.
```

Still blocked:

```text
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark result;
level3 self-identification;
checkpoint/profile promotion.
```
