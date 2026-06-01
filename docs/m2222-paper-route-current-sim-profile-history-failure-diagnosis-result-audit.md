# M2222 Paper-Route Current-Sim Profile/History Failure Diagnosis Result Audit

- status: completed
- decision: `current_sim_profile_history_failure_diagnosis_audit_route_to_recurrent_profile_artifact_audit`
- manifest: `experiments/manifests/m2222-paper-route-current-sim-profile-history-failure-diagnosis-result-audit.json`
- parent result: `runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/summary.json`
- reset in M2222: `false`
- measured execution in M2222: `false`
- policy action executed in M2222: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2221 is complete and claim-safe:

```text
result_class: current_sim_profile_history_failure_diagnosis_pass
scene_candidate_count: 9
profile_metric_row_count: 54
history_metric_row_count: 36
pair_delta_row_count: 45
l3_failure_breakdown_row_count: 9
l3_online_success_count: 0
l3_reset_success_count: 0
l2_window_25_success_count: 360
l2_window_50_success_count: 153
l3_zero_success_confirmed: true
l3_reset_equivalent_to_online: true
finite_window_support_visible: true
failure_mode_counts: early_offtrack_failure 21, late_offtrack_or_noncompletion 3, supported_success 30
ranking_admissible_count: 0
winner_selected: false
guardrail_violation_count: 0
```

The claim boundary is also clean: M2221 blocks controller-family ranking,
winner selection, finite-window-vs-GRU conclusion, paper-level benchmark result,
and level3 self-identification.

## Route Decision

M2222 routes to a recurrent-profile artifact audit, not to repair or rerun.

Reason:

```text
L3_online_gru success: 0
L3_reset_control success: 0
L3 reset equivalent to online: true
finite-window support visible: true
```

The immediate scientific question is no longer whether the current diagnostic
panel contains finite-window support. It does. The blocker is why the L3 online
GRU profile and its reset control are both zero-success and outcome-equivalent
on this panel. Before any recurrent repair, retraining, ranking, or conclusion,
the project must audit:

```text
profile-to-checkpoint mapping
profile config semantics
reset-control alias/correction path
evaluated checkpoint provenance
GRU/recurrent flag and hidden-state use
observation/profile compatibility
training lineage for the L3 checkpoint
whether M2221 is seeing a true recurrent-profile failure or an artifact/config mismatch
```

## Explicit Non-Claims

M2222 does not claim:

```text
finite-window beats GRU;
GRU/recurrent history is useless;
the current panel is ranking-ready;
the current panel is paper-level evidence;
the driver has or lacks level3 self-identification.
```

The only supported claim is narrower:

```text
M2221 localizes a diagnostic recurrent-profile failure pattern that requires
artifact/config/training audit before further comparison.
```

## Next Step

M2223 should perform an artifact-only recurrent-profile audit. It should read
existing materialization/readiness/profile config artifacts and produce a
route decision:

```text
if checkpoint/config/provenance mismatch is found:
  route to no-rollout metadata/config repair before any rerun.

if L3 online and reset profiles are correctly configured but checkpoint is weak:
  route to recurrent-profile training-lineage or checkpoint-quality audit.

if hidden-state handling is wrong:
  route to recurrent evaluation harness repair.

if artifacts are clean:
  route to a bounded recurrent-profile negative-result synthesis or a fresh
  training-design branch, not to ranking.
```

Reset, rollout, measured execution, training, ranking, paper claims,
finite-window-vs-GRU verdicts, and level3 self-ID claims remain blocked.
