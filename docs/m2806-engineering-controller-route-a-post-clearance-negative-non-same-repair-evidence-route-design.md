# M2806 Engineering Controller Route A Post-Clearance Negative Non-Same-Repair Evidence Route Design

## Metadata

- status: completed
- decision: `admit_m2807_post_clearance_negative_non_same_repair_cross_axis_bounded_execution_preflight`
- manifest: `experiments/manifests/m2806-engineering-controller-route-a-post-clearance-negative-non-same-repair-evidence-route-design.json`
- design doc: `docs/m2806-engineering-controller-route-a-post-clearance-negative-non-same-repair-evidence-route-design.md`
- parent audit: `docs/m2805-engineering-controller-route-a-post-clearance-corrective-readiness-index-materialization-result-audit.md`
- parent readiness index: `runs/m2804_engineering_controller_route_a_post_clearance_corrective_readiness_index/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2807-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-bounded-execution-preflight.json`
- next: `m2807-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-bounded-execution-preflight`

## Design Premise

M2805 accepts M2804 as complete and claim-safe readiness/admission indexing
only. M2804 reanalyzed existing artifacts, wrote 15 evidence rows, 11
deliverable rows, 7 blocker rows, 7 next-action rows, 26 claim-boundary rows,
and 38 passing gates, but it did not reset, step, rollout, validate, train,
rank, promote, or claim driver performance.

The accepted M2801/M2802 clearance-localized corrective branch remains
negative:

```text
candidate-minus-source obstacle clearance: 23 positive / 49 negative
candidate-minus-source mean: -0.00365399786071096
candidate-minus-M2791-start obstacle clearance: 23 positive / 49 negative
candidate-minus-M2791-start mean: -0.001043581525003352
stable_avoidable negative rows against source: 4
stable_avoidable negative rows against M2791 start: 2
```

M2806 is design-only. It does not execute reset, step, policy action, rollout,
replay, validation, training, PPO, source build, adapter probe, external
simulation, ranking, winner selection, checkpoint promotion, or success-rate
verdict computation.

The route decision follows `docs/post-m2470-route-plan.md`: Route A should
continue as the engineering controller mainline, while current-sim readiness
artifacts must not become the main loop. The next evidence step must therefore
produce a bounded Route A closed-loop diagnostic surface that is not another
same clearance-localized corrective update, not another same-style fresh-holdout
triad panel, and not a relabeling of readiness rows.

## Source Criteria

M2807 may use only these source surfaces for candidate selection, exclusion,
and guardrails:

```text
docs/m2806-engineering-controller-route-a-post-clearance-negative-non-same-repair-evidence-route-design.md
docs/m2805-engineering-controller-route-a-post-clearance-corrective-readiness-index-materialization-result-audit.md
runs/m2804_engineering_controller_route_a_post_clearance_corrective_readiness_index/summary.json
runs/m2804_engineering_controller_route_a_post_clearance_corrective_readiness_index/blocker_matrix.csv
runs/m2804_engineering_controller_route_a_post_clearance_corrective_readiness_index/next_action_admission_rows.csv
runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv
runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/candidate_execution_rows.csv
runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/execution_candidate_rows.csv
runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/candidate_execution_rows.csv
runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight/candidate_execution_rows.csv
docs/post-m2470-route-plan.md
```

The executable policy-under-test remains the existing `L3_online_gru` row from
M1690. M2807 must not substitute another profile, compare controller families,
rank L0/L1/L2/L3, or treat `L3_online_gru` as a paper self-ID claim. The
selection is a Route A engineering diagnostic protocol only.

Each admitted candidate must satisfy:

```text
profile_name: L3_online_gru
config_exists: True
checkpoint_exists: True
profile_specific_tuning: False
actor input change required: false
hidden/oracle actor input required: false
stress-axis labels actor-visible: false
clearance labels actor-visible: false
private holdout used: false
```

## Non-Same-Repair Exclusion Rules

M2807 must exclude the same clearance-localized repair loop and the already
used Route A panels before execution.

The exclusion set must include task-source ids from:

```text
M2737 candidate_execution_rows.csv
M2746 execution_candidate_rows.csv
M2746 candidate_execution_rows.csv
M2753 candidate_execution_rows.csv
```

The M2801/M2802 triad rows are not keyed by M1690 `task_source_id`, so M2807
must exclude them by route and surface instead: no M2799 candidate update, no
M2801 source/start/candidate triad comparison, no clearance-localized
corrective retraining, and no same-style triad delta panel.

If a selected task-source id appears in any prior-panel exclusion set, M2807
must account for it as a failed candidate and must not substitute a nearby row.
Protected mitigation and HF3 blocker rows remain guardrails only and are never
ordinary execution candidates.

## Candidate Surface

M2806 admits exactly 12 fixed M1690 `L3_online_gru` task-source ids for M2807.
The ids were checked against the live M1690 workload and prior M2737/M2746/M2753
surfaces on 2026-06-06; all are present, have `config_exists=True`,
`checkpoint_exists=True`, and have no prior task-source overlap.

```text
m1680-spec-0014  T4  actuator_delay_step|capability_step_up              reveal_plus_4
m1680-spec-0016  T4  capability_step_down|t4_actuator_delay_response     mapping_window_unspecified
m1680-spec-0018  T4  t4_actuator_delay_response|capability_step_up       mapping_window_unspecified
m1680-spec-0022  T4  actuator_delay_step|t4_capability_step_temporal     mapping_window_unspecified
m1680-spec-0026  T4  t4_capability_step_temporal|capability_step_down    mapping_window_unspecified
m1680-spec-0032  T4  t4_actuator_delay_response|capability_step_up       mapping_window_unspecified
m1680-spec-0048  T5  curved_boundary_obstacle|t5_boundary_axis_retarget  decision_minus_32
m1680-spec-0051  T5  actuator_delay_step|t5_near_boundary_warmup         reveal_plus_4
m1680-spec-0052  T5  capability_step_down|t5_near_boundary_warmup        decision_minus_24
m1680-spec-0053  T5  curved_boundary_obstacle|t5_boundary_axis_retarget  decision_minus_32
m1680-spec-0058  T5  capability_step_down|t5_near_boundary_warmup        decision_minus_24
m1680-spec-0063  T5  actuator_delay_step|t5_near_boundary_warmup         reveal_plus_4
```

This surface intentionally differs from the failed same-repair branch:

```text
not M2799 clearance-localized corrective training
not M2801 source/start/candidate triad delta replay
not another M2801 seed extension
not M2753 selected task-source ids
not M2737/M2746 selected task-source ids
not protected mitigation or HF3 blocker execution
```

Stress-axis tags are diagnostic artifact tags only:

```text
actuator_delay_or_response:
  m1680-spec-0014
  m1680-spec-0016
  m1680-spec-0018
  m1680-spec-0022
  m1680-spec-0032
  m1680-spec-0051
  m1680-spec-0063

capability_step_or_authority:
  m1680-spec-0014
  m1680-spec-0016
  m1680-spec-0018
  m1680-spec-0026
  m1680-spec-0032
  m1680-spec-0052
  m1680-spec-0058

late_boundary_or_near_boundary:
  m1680-spec-0048
  m1680-spec-0051
  m1680-spec-0052
  m1680-spec-0053
  m1680-spec-0058
  m1680-spec-0063

curved_or_retargeted_obstacle:
  m1680-spec-0048
  m1680-spec-0053
```

These tags must not be actor inputs, reward inputs, target labels, blocker
labels, route-decision labels, progress labels, success labels, ranking groups,
or verdict labels.

## M2807 Execution Policy

M2807 must be a bounded implementation plus execution preflight. It may create
a dedicated runner or parameterize the M2753 runner, but it must not run M2753
directly with M2753 artifact labels.

Required M2807 implementation properties:

```text
milestone labels begin with m2807
candidate ids begin with m2807
resolution ids begin with m2807
guard ids begin with m2807
claim ids begin with m2807
gate ids begin with m2807
doc title and claim boundary name M2807, not M2753
selected task-source ids are exactly the 12 ids in this document
source guardrails include M2804/M2805 blockers and M2737/M2746/M2753 exclusions
```

Execution policy:

```text
one diagnostic rollout per resolved candidate row
eval_seed_base: 280700
device: cpu unless explicitly changed by a later manifest
no mining additional rows
no resampling until success
no active config overwrite
no profile-specific tuning
no actor input or action contract change
write failure rows instead of substituting candidates
register a separate M2808 result-audit manifest before interpretation
```

M2807 may record reset, step, policy action, and rollout fields only for the 12
resolved diagnostic rows. It must not execute replay, validation, training,
PPO, source build, adapter probe, external simulation, ranking, winner
selection, checkpoint promotion, or success-rate verdict computation.

## Output Artifacts

M2807 should write M2807-specific artifacts under:

```text
runs/m2807_engineering_controller_route_a_post_clearance_negative_non_same_repair_cross_axis_bounded_execution_preflight/
```

Required output families:

```text
summary.json
non_same_repair_candidate_rows.csv
execution_candidate_resolution_rows.csv
candidate_execution_rows.csv
candidate_execution_failure_rows.csv
stress_axis_aggregate_rows.csv
prior_surface_exclusion_rows.csv
blocker_guard_rows.csv
actor_contract_guard_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
run_state.json
docs/m2807-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-bounded-execution-preflight.md
```

Artifact completeness is not validation readiness and not performance evidence.
Any M2807 result must route to M2808 for audit before interpretation.

## Actor Contract Guard

M2807 must preserve:

```text
P0 observation shape: 72
action shape: 3
hidden_oracle_actor_input_detected: false
actor_input_changed: false
deployed action contract changed: false
```

Allowed actor-visible information remains the already admitted Route A
human-view control surface: ego response, actuator state, previous physical
commands, ego-frame road/free-space/obstacle geometry, and recurrent/history
state.

M2807 must not add any of these to actor input:

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
clearance labels
scenario-role labels
oracle feasibility
AEB/AES/drift labels
TTC
reference trajectory
path error
heading error
path curvature
required clearance
precomputed success or progress labels
verdict labels
```

## Blocker Boundary

M2807 must carry these as blockers or guardrails, not ordinary denominators:

```text
M2801/M2802 negative obstacle-clearance evidence
stable_avoidable retention risk
M2803/M2804 same clearance-localized repair closure
protected mitigation blocker
HF3 source dependency blocker
M2737/M2746/M2753 prior-panel task-source exclusions
```

M2807 may report diagnostic termination and metric fields for the 12 selected
rows, but it must not collapse blocker rows into success denominators or use
stress-axis aggregates to rank sources, tasks, profiles, checkpoints, or
scenario roles.

## Rejected Interpretations

M2806 rejects these interpretations:

```text
M2806 proves repair success: false
M2806 proves driver performance: false
M2806 validates the controller: false
M2806 admits another clearance-localized corrective update: false
M2806 admits another same-style triad panel: false
M2806 ranks controller families, task families, source edges, stress axes, or checkpoints: false
M2806 selects a winner or promotes a checkpoint: false
M2806 supports paper evidence or finite-window-vs-GRU evidence: false
M2806 supports current-sim or high-fidelity validation verdicts: false
M2806 supports full ideal driver completion or level3 self-identification: false
```

The only allowed M2806 claim is that a bounded, non-same-repair M2807 execution
preflight is admitted with the fixed candidate surface and guardrails above.
