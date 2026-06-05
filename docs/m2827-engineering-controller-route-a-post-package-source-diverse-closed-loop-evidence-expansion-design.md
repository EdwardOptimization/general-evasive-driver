# M2827 Engineering Controller Route A Post-Package Source-Diverse Closed-Loop Evidence Expansion Design

## Metadata

- status: completed
- decision: `admit_m2828_post_package_source_diverse_closed_loop_evidence_expansion_preflight`
- manifest: `experiments/manifests/m2827-engineering-controller-route-a-post-package-source-diverse-closed-loop-evidence-expansion-design.json`
- design doc: `docs/m2827-engineering-controller-route-a-post-package-source-diverse-closed-loop-evidence-expansion-design.md`
- parent synthesis: `docs/m2826-engineering-controller-route-a-post-recoverability-negative-limited-package-branch-synthesis.md`
- parent package audit: `docs/m2825-engineering-controller-route-a-post-recoverability-negative-limited-package-materialization-result-audit.md`
- parent package summary: `runs/m2824_engineering_controller_route_a_post_recoverability_negative_limited_package/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2828-engineering-controller-route-a-post-package-source-diverse-closed-loop-evidence-expansion-preflight.json`
- next: `m2828-engineering-controller-route-a-post-package-source-diverse-closed-loop-evidence-expansion-preflight`

## Design Premise

M2826 closes the M2823-M2825 limited package branch as complete and
claim-safe process evidence only. The package branch produced useful local
boundary and limitation artifacts, but it did not add closed-loop driver
evidence, repair the controller, or change the Route A capability verdict.

The accepted package limitation surface remains active:

```text
M2824 package content covered: 6/6
M2824 limitation groups covered: 4/4
M2824 known blocker rows: 5
M2824 recoverability limitation rows: 7
M2824 claim rows: 27
M2824 package gates: 24
M2816 post-event traces: 7
M2816 recoverability-window availability: 0
M2816 recoverability success: 0
M2816 diagnostic collision count: 1
M2816 diagnostic offtrack termination count: 5
M2804 prior blockers: active
M2638 HF3 source dependency blocker: active
```

M2827 is design-only. It does not execute reset, step, policy action, rollout,
replay, validation, training, PPO, source build, adapter probe, external
simulation, ranking, winner selection, checkpoint promotion, package
publication, or success-rate verdict computation.

The route decision follows `docs/post-m2470-route-plan.md`: Route A must return
to engineering controller evidence and avoid letting static package/process
artifacts become the main loop. The next step must therefore be a bounded
closed-loop diagnostic preflight over a fresh non-same-surface source-diverse
candidate set.

## Source Criteria

M2828 may use only these source surfaces for candidate selection, exclusion,
and guardrails:

```text
docs/m2827-engineering-controller-route-a-post-package-source-diverse-closed-loop-evidence-expansion-design.md
docs/m2826-engineering-controller-route-a-post-recoverability-negative-limited-package-branch-synthesis.md
docs/m2825-engineering-controller-route-a-post-recoverability-negative-limited-package-materialization-result-audit.md
runs/m2824_engineering_controller_route_a_post_recoverability_negative_limited_package/summary.json
runs/m2824_engineering_controller_route_a_post_recoverability_negative_limited_package/known_blocker_disclosure_rows.csv
runs/m2824_engineering_controller_route_a_post_recoverability_negative_limited_package/recoverability_limitations_rows.csv
runs/m2824_engineering_controller_route_a_post_recoverability_negative_limited_package/actor_action_contract_rows.csv
runs/m2824_engineering_controller_route_a_post_recoverability_negative_limited_package/claim_boundary_rows.csv
runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv
runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/candidate_execution_rows.csv
runs/m2807_engineering_controller_route_a_post_clearance_negative_non_same_repair_cross_axis_bounded_execution_preflight/candidate_execution_rows.csv
runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/instrumented_execution_rows.csv
docs/post-m2470-route-plan.md
```

The executable policy-under-test remains the existing `L3_online_gru` row from
M1690, backed by the current Route A source checkpoint lineage. M2828 must not
substitute another profile, compare controller families, rank L0/L1/L2/L3, or
turn `L3_online_gru` into a paper self-ID claim. This is Route A engineering
diagnostic evidence only.

Each admitted candidate must satisfy:

```text
profile_name: L3_online_gru
config_exists: True
checkpoint_exists: True
profile_specific_tuning: False
actor input change required: false
hidden/oracle actor input required: false
package labels actor-visible: false
recoverability labels actor-visible: false
stress-axis labels actor-visible: false
private holdout used: false
```

## Prior-Surface Exclusion Rules

M2828 must exclude already used Route A closed-loop task-source surfaces before
execution. The exclusion set must include task-source ids from:

```text
M2737 candidate_execution_rows.csv
M2807 candidate_execution_rows.csv
M2816 instrumented_execution_rows.csv
```

The M2816 rows intentionally overlap M2807. They still remain explicit because
M2816 is the immediate negative recoverability-window branch that M2828 must
not repair or rerank.

M2828 must also exclude by route rather than only by key:

```text
no M2799 clearance-localized corrective update
no M2801 source/start/candidate triad replay
no M2816 same recoverability-window rerun
no package publication or package audit loop
no protected mitigation rows as ordinary execution candidates
no HF3 blocker rows as ordinary execution candidates
```

If a selected task-source id appears in any prior-surface exclusion set, M2828
must account for it as a failed candidate and must not substitute a nearby row.

## Candidate Surface

M2827 admits exactly 16 fixed M1690 `L3_online_gru` task-source ids for M2828.
The ids were checked against the live M1690 workload and the M2737/M2807/M2816
prior surfaces on 2026-06-06. All are present, have `config_exists=True`, have
`checkpoint_exists=True`, have `profile_specific_tuning=False`, and have no
prior task-source overlap.

```text
m1680-spec-0007  T4  actuator_delay_step|capability_step_up           reveal_plus_4
m1680-spec-0009  T4  capability_step_down|t4_actuator_delay_response  mapping_window_unspecified
m1680-spec-0011  T4  t4_actuator_delay_response|capability_step_up    mapping_window_unspecified
m1680-spec-0013  T4  t4_staged_warmup_capability|capability_step_up   mapping_window_unspecified
m1680-spec-0015  T4  actuator_delay_step|t4_capability_step_temporal  mapping_window_unspecified
m1680-spec-0017  T4  t4_actuator_delay_response|actuator_delay_step   mapping_window_unspecified
m1680-spec-0021  T4  actuator_delay_step|capability_step_up           reveal_plus_4
m1680-spec-0023  T4  capability_step_down|t4_actuator_delay_response  mapping_window_unspecified
m1680-spec-0037  T5  brake_fade_or_loss_proxy|late_reveal_boundary    mapping_window_unspecified
m1680-spec-0039  T5  curved_boundary_obstacle|drive_loss_proxy        mapping_window_unspecified
m1680-spec-0042  T5  t5_boundary_axis_retarget|drive_loss_proxy       mapping_window_unspecified
m1680-spec-0044  T5  actuator_delay_step|t5_near_boundary_warmup      reveal_plus_4
m1680-spec-0046  T5  capability_step_down|t5_near_boundary_warmup     decision_minus_24
m1680-spec-0047  T5  curved_boundary_obstacle|drive_loss_proxy        mapping_window_unspecified
m1680-spec-0049  T5  drive_loss_proxy|curved_boundary_obstacle        mapping_window_unspecified
m1680-spec-0050  T5  t5_boundary_axis_retarget|drive_loss_proxy       mapping_window_unspecified
```

The surface intentionally differs from the recently exhausted loops:

```text
not M2737 post-negative source-diverse candidates
not M2807 post-clearance non-same-repair candidates
not M2816 recoverability-window instrumented reruns
not M2799/M2801 clearance-localized corrective branch rows
not another package materialization or package audit
not protected mitigation or HF3 blocker execution
```

Diagnostic tags for M2828:

```text
t4_actuator_delay_or_response:
  m1680-spec-0007
  m1680-spec-0011
  m1680-spec-0015
  m1680-spec-0017
  m1680-spec-0021

t4_capability_or_staged_warmup:
  m1680-spec-0007
  m1680-spec-0009
  m1680-spec-0013
  m1680-spec-0021
  m1680-spec-0023

t5_loss_or_boundary:
  m1680-spec-0037
  m1680-spec-0039
  m1680-spec-0042
  m1680-spec-0047
  m1680-spec-0049
  m1680-spec-0050

t5_near_boundary_or_delay:
  m1680-spec-0044
  m1680-spec-0046
```

These tags are evaluator artifact tags only. They must not be actor inputs,
reward inputs, target labels, blocker labels, route-decision labels, progress
labels, success labels, ranking groups, or verdict labels.

## M2828 Execution Policy

M2828 must be a bounded implementation plus execution preflight. It may reuse
the M2807 execution pattern, but all milestone labels, artifact names, claim
text, selected ids, and guardrail accounting must be M2828-specific.

Required M2828 implementation properties:

```text
milestone labels begin with m2828
candidate ids begin with m2828
resolution ids begin with m2828
guard ids begin with m2828
claim ids begin with m2828
gate ids begin with m2828
doc title and claim boundary name M2828
selected task-source ids are exactly the 16 ids in this document
prior-surface guardrails include M2737, M2807, M2816, package limitations, and
  HF3 blockers
```

Execution policy:

```text
one diagnostic rollout per resolved candidate row
eval_seed_base: 282800
device: cpu unless explicitly changed by a later manifest
no mining additional rows
no resampling until success
no active config overwrite
no profile-specific tuning
no actor input or action contract change
write failure rows instead of substituting candidates
register a separate M2829 result-audit manifest before interpretation
```

M2828 may record reset, step, policy action, and rollout fields only for the 16
resolved diagnostic rows. It must not execute replay, validation, training,
PPO, source build, adapter probe, external simulation, ranking, winner
selection, checkpoint promotion, package publication, or success-rate verdict
computation.

## Output Artifacts

M2828 should write M2828-specific artifacts under:

```text
runs/m2828_engineering_controller_route_a_post_package_source_diverse_closed_loop_evidence_expansion_preflight/
```

Required output families:

```text
summary.json
post_package_candidate_rows.csv
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
docs/m2828-engineering-controller-route-a-post-package-source-diverse-closed-loop-evidence-expansion-preflight.md
```

Artifact completeness is not validation readiness and not performance evidence.
Any M2828 result must route to M2829 for audit before interpretation.

## Actor Contract Guard

M2828 must preserve:

```text
P0 observation shape: 72
action shape: 3
hidden_oracle_actor_input_detected: false
actor_input_changed: false
deployed action contract changed: false
```

Allowed actor-visible information remains the admitted Route A human-view
control surface: ego response, actuator state, previous physical commands,
ego-frame road/free-space/obstacle geometry, and recurrent/history state.

M2828 must not add any of these to actor input:

```text
friction or mu
mass
center of gravity
tire stiffness
brake scale
drive scale
steering delay
drive delay
sensor noise labels
actuator delay labels
source edge labels
stress-axis labels
scenario-role labels
package labels
recoverability labels
blocker labels
route-decision labels
success/progress/verdict labels
TTC
required clearance
reference trajectory
oracle stopping distance
```

## Claim Boundary

M2828 may claim only:

```text
bounded Route A post-package source-diverse closed-loop diagnostic execution
artifact completeness
candidate accounting over the fixed 16-row surface
actor and claim boundary preservation
diagnostic outcome/failure taxonomy rows before audit
```

M2828 must not claim:

```text
package publication
repair success
recoverability success
driver performance
validation readiness
validation result
ranking or winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU result
current-response sufficiency
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```

## Follow-Up

M2827 registers:

```text
experiments/manifests/m2828-engineering-controller-route-a-post-package-source-diverse-closed-loop-evidence-expansion-preflight.json
```

M2828 should execute the fixed 16-row diagnostic surface and then register a
separate M2829 result-audit manifest before any interpretation. If M2828 cannot
account for the fixed surface without actor contract or claim-boundary
violations, it must stop or route to artifact repair instead of substituting
rows or weakening gates.
