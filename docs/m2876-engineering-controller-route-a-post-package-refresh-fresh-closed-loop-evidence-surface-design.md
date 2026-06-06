# M2876 Engineering Controller Route A Post-Package Refresh Fresh Closed-Loop Evidence Surface Design

## Metadata

- status: completed
- decision: `admit_m2877_post_package_refresh_fresh_closed_loop_evidence_preflight`
- manifest: `experiments/manifests/m2876-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-evidence-surface-design.json`
- design artifact: `docs/m2876-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-evidence-surface-design.md`
- parent synthesis: `docs/m2875-engineering-controller-route-a-post-localized-response-prediction-limited-baseline-package-refresh-branch-synthesis.md`
- package refresh audit: `docs/m2874-engineering-controller-route-a-post-localized-response-prediction-limited-baseline-package-refresh-materialization-result-audit.md`
- package refresh summary: `runs/m2873_engineering_controller_route_a_post_localized_response_prediction_limited_baseline_package_refresh/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2877-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-evidence-preflight.json`
- next: `m2877-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-evidence-preflight`

## Design Premise

M2875 closes the package refresh branch as complete and claim-safe process
evidence only. The package rows are now useful boundary evidence, but they do
not change closed-loop driver capability evidence.

M2876 is design-only. It does not execute reset, step, policy action, rollout,
replay, validation, training, PPO, source build, adapter probe, external
simulation, ranking, winner selection, checkpoint promotion, package
publication, or success-rate verdict computation.

The next Route A step must therefore be a bounded evidence-producing preflight
over a fixed non-same-surface diagnostic surface. It must not continue the
package-process branch.

## Source Criteria

M2877 may use only these source surfaces for candidate selection, exclusion,
and guardrails:

```text
docs/m2876-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-evidence-surface-design.md
docs/m2875-engineering-controller-route-a-post-localized-response-prediction-limited-baseline-package-refresh-branch-synthesis.md
docs/m2874-engineering-controller-route-a-post-localized-response-prediction-limited-baseline-package-refresh-materialization-result-audit.md
runs/m2873_engineering_controller_route_a_post_localized_response_prediction_limited_baseline_package_refresh/summary.json
runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv
runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/candidate_execution_rows.csv
runs/m2807_engineering_controller_route_a_post_clearance_negative_non_same_repair_cross_axis_bounded_execution_preflight/candidate_execution_rows.csv
runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/instrumented_execution_rows.csv
runs/m2828_engineering_controller_route_a_post_package_source_diverse_closed_loop_evidence_expansion_preflight/candidate_execution_rows.csv
runs/m2838_engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_evidence_preflight/candidate_execution_rows.csv
runs/m2868_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_candidate_closed_loop_delta_panel/paired_execution_rows.csv
docs/post-m2470-route-plan.md
```

The executable policy-under-test remains `L3_online_gru` from M1690. M2877
must not compare profiles, rank controller families, promote a checkpoint, or
turn `L3_online_gru` into a Route B paper/self-ID claim.

Each admitted candidate must satisfy:

```text
profile_name: L3_online_gru
config_exists: True
checkpoint_exists: True
profile_specific_tuning: False
actor input change required: false
hidden/oracle actor input required: false
package labels actor-visible: false
blocker labels actor-visible: false
diagnostic labels actor-visible: false
route labels actor-visible: false
success/progress labels actor-visible: false
verdict labels actor-visible: false
private holdout used: false
```

## Prior-Surface Exclusion Rules

M2877 must exclude every task-source id already executed or paired in these
Route A diagnostic surfaces:

```text
M2737 candidate_execution_rows.csv
M2807 candidate_execution_rows.csv
M2816 instrumented_execution_rows.csv
M2828 candidate_execution_rows.csv
M2838 candidate_execution_rows.csv
M2868 paired_execution_rows.csv
```

The live exclusion set contains 61 unique task-source ids. The remaining
`L3_online_gru` candidate surface contains 11 task-source ids. M2877 must not
pad the panel back to 16 rows by reusing a prior surface.

M2877 must also exclude by route rather than only by key:

```text
no M2799 clearance-localized corrective update
no M2801 source/start/candidate triad replay
no M2816 recoverability-window rerun
no M2828 post-package row replay
no M2838 post-HF3-stop row replay
no M2868 localized-response-prediction paired row replay
no package publication or package audit loop
no protected mitigation rows as ordinary execution candidates
no HF3 blocker rows as ordinary execution candidates
```

If a selected task-source id appears in any prior-surface exclusion set, M2877
must account for it as a failed candidate and must not substitute a nearby row.

## Candidate Surface

M2876 admits exactly 11 fixed M1690 `L3_online_gru` task-source ids for M2877.
These are all remaining `L3_online_gru` rows after excluding M2737, M2807,
M2816, M2828, M2838, and M2868 task-source ids. All selected rows are present
in M1690, have `config_exists=True`, have `checkpoint_exists=True`, and have
`profile_specific_tuning=False`.

```text
m1680-spec-0001  T4  actuator_delay_step|t4_capability_step_temporal     mapping_window_unspecified
m1680-spec-0003  T4  t4_actuator_delay_response|actuator_delay_step      mapping_window_unspecified
m1680-spec-0008  T4  actuator_delay_step|t4_capability_step_temporal     mapping_window_unspecified
m1680-spec-0010  T4  t4_actuator_delay_response|actuator_delay_step      mapping_window_unspecified
m1680-spec-0043  T5  t5_near_boundary_warmup|t5_boundary_axis_retarget   mapping_window_unspecified
m1680-spec-0045  T5  brake_fade_or_loss_proxy|late_reveal_boundary       mapping_window_unspecified
m1680-spec-0067  T5  capability_step_down|t5_near_boundary_warmup        decision_minus_24
m1680-spec-0068  T5  curved_boundary_obstacle|t5_boundary_axis_retarget  decision_minus_32
m1680-spec-0069  T5  actuator_delay_step|t5_near_boundary_warmup         reveal_plus_4
m1680-spec-0070  T5  capability_step_down|t5_near_boundary_warmup        decision_minus_24
m1680-spec-0071  T5  curved_boundary_obstacle|t5_boundary_axis_retarget  decision_minus_32
```

Diagnostic tags for M2877:

```text
t4_actuator_delay_or_response:
  m1680-spec-0001
  m1680-spec-0003
  m1680-spec-0008
  m1680-spec-0010

t5_near_boundary_or_delay:
  m1680-spec-0043
  m1680-spec-0067
  m1680-spec-0069
  m1680-spec-0070

t5_loss_or_boundary:
  m1680-spec-0045
  m1680-spec-0068
  m1680-spec-0071

t5_retargeted_boundary:
  m1680-spec-0043
  m1680-spec-0068
  m1680-spec-0071
```

These tags are evaluator artifact tags only. They must not be actor inputs,
reward inputs, target labels, blocker labels, route-decision labels, progress
labels, success labels, ranking groups, or verdict labels.

## M2877 Execution Policy

M2877 must be a bounded implementation plus execution preflight. It should
implement a new M2877 runner rather than reuse the M2828 runner with stale
M2828 labels.

Required M2877 implementation properties:

```text
milestone labels begin with m2877
candidate ids begin with m2877
resolution ids begin with m2877
guard ids begin with m2877
claim ids begin with m2877
gate ids begin with m2877
doc title and claim boundary name M2877
selected task-source ids are exactly the 11 ids in this document
prior-surface guardrails include M2737 M2807 M2816 M2828 M2838 M2868 package
  limitations protected blockers and HF3 blockers
```

Execution policy:

```text
one diagnostic rollout per resolved candidate row
eval_seed_base: 287700
device: cpu unless explicitly changed by a later manifest
no mining additional rows
no resampling until success
no active config overwrite
no profile-specific tuning
no actor input or action contract change
write failure rows instead of substituting candidates
register a separate M2878 result-audit manifest before interpretation
```

M2877 may record reset, step, policy action, and rollout fields only for the 11
resolved diagnostic rows. It must not execute replay, validation, training,
PPO, source build, adapter probe, external simulation, ranking, winner
selection, checkpoint promotion, package publication, or success-rate verdict
computation.

## Output Artifacts

M2877 should write M2877-specific artifacts under:

```text
runs/m2877_engineering_controller_route_a_post_package_refresh_fresh_closed_loop_evidence_preflight/
```

Required output families:

```text
summary.json
fresh_candidate_rows.csv
execution_candidate_resolution_rows.csv
candidate_execution_rows.csv
candidate_execution_failure_rows.csv
scenario_role_metric_rows.csv
failure_taxonomy_rows.csv
prior_surface_exclusion_rows.csv
package_limitation_guard_rows.csv
actor_contract_guard_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
run_state.json
docs/m2877-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-evidence-preflight.md
experiments/manifests/m2878-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-evidence-result-audit.json
```

## Claim Boundary

M2876 admits M2877 only as Route A bounded diagnostic execution. The allowed
claim is:

```text
M2877 produced complete bounded diagnostic execution artifacts over the fixed
post-package-refresh 11-row fresh M1690 L3_online_gru surface while preserving
actor and claim boundaries.
```

Forbidden interpretations:

```text
package publication
repair success
recoverability success
localized-response-prediction success
driver performance
validation readiness or validation result
checkpoint ranking or promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-response sufficiency
current-sim verdict
high-fidelity validation
full ideal driver completion
level3 self-identification
```

## Next Route

M2876 admits:

```text
m2877-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-evidence-preflight
```

M2877 should implement and execute the fixed 11-row diagnostic surface and
register M2878 result audit before interpretation.
