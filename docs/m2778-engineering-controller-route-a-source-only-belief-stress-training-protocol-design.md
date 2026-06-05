# M2778 Engineering Controller Route A Source-Only Belief-Stress Training Protocol Design

## Metadata

- status: completed
- decision: `admit_source_only_belief_stress_training_admission_pack_materialization`
- manifest: `experiments/manifests/m2778-engineering-controller-route-a-source-only-belief-stress-training-protocol-design.json`
- design doc: `docs/m2778-engineering-controller-route-a-source-only-belief-stress-training-protocol-design.md`
- parent synthesis: `docs/m2777-engineering-controller-route-a-source-only-action-response-belief-intervention-branch-synthesis.md`
- parent audit: `docs/m2776-engineering-controller-route-a-source-only-action-response-belief-intervention-delta-panel-materialization-result-audit.md`
- parent summary: `runs/m2775_engineering_controller_route_a_source_only_action_response_belief_intervention_delta_panel_materialization/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- self-ID route plans: `docs/self-id-go-no-go-paper-route-plan.md`, `docs/paper-route-finite-window-vs-gru-plan.md`
- follow-up manifest: `experiments/manifests/m2779-engineering-controller-route-a-source-only-belief-stress-training-admission-pack-materialization-preflight.json`
- next: `m2779-engineering-controller-route-a-source-only-belief-stress-training-admission-pack-materialization-preflight`

## Design Premise

M2777 accepts M2772-M2776 as a complete and claim-safe source-only
action-response belief intervention branch, but rejects another no-new-data
intervention/delta reanalysis. The branch produced modest source-only
sensitivity:

```text
M2773:
  candidate rows: 32
  intervention conditions: 4
  execution rows: 128
  failure rows: 0
  action-response trace rows: 10240
  collision diagnostic rows: 32
  road-departure diagnostic rows: 68

M2775:
  delta rows: 96
  matched trace pairs: 7680
  road-departure removed: 4
  road-departure added: 0
  collision added: 0
  collision removed: 0
  action L1 mean: 0.0383708570
  ego response L2 mean: 0.1288659872
```

This is useful evidence for designing the next Route A surface, but it is not
driver performance, validation readiness, paper evidence, high-fidelity
evidence, finite-window-vs-GRU evidence, full-driver completion, or level3
self-identification.

M2778 is design-only. It does not reset, step, run policy actions, rollout,
replay, validate, train, run PPO, build source, probe adapters, run external
simulation, rank interventions, select winners, promote checkpoints, compute
success-rate verdicts, or claim repair success, driver performance, paper
evidence, current-sim validation, high-fidelity validation, full ideal driver
completion, or self-identification.

## Protocol Goal

The next useful Route A step is a source-only belief-stress training/admission
pack. The pack should transform M2773/M2775 diagnostic artifacts into a
future-action contract:

```text
source-only intervention rows
  -> belief-stress admission rows
  -> curriculum/stress buckets
  -> actor and claim guards
  -> follow-up decision: materialize fresh execution/training evidence,
     route to artifact repair, or stop
```

The pack must not train. It must not claim that the M2775 deltas improved the
driver. Its purpose is to make the next training or fresh-data milestone
auditable before any PPO, rollout, validation, or promotion is admitted.

## Candidate Input Surface

M2779 may consume only the following artifacts:

```text
docs/m2778-engineering-controller-route-a-source-only-belief-stress-training-protocol-design.md
docs/m2777-engineering-controller-route-a-source-only-action-response-belief-intervention-branch-synthesis.md
docs/m2776-engineering-controller-route-a-source-only-action-response-belief-intervention-delta-panel-materialization-result-audit.md
runs/m2775_engineering_controller_route_a_source_only_action_response_belief_intervention_delta_panel_materialization/summary.json
runs/m2775_engineering_controller_route_a_source_only_action_response_belief_intervention_delta_panel_materialization/intervention_delta_rows.csv
runs/m2775_engineering_controller_route_a_source_only_action_response_belief_intervention_delta_panel_materialization/role_dynamics_delta_aggregate_rows.csv
runs/m2775_engineering_controller_route_a_source_only_action_response_belief_intervention_delta_panel_materialization/intervention_condition_delta_aggregate_rows.csv
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/summary.json
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/source_only_candidate_rows.csv
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/intervention_execution_rows.csv
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/action_response_trace_rows.csv
```

M2779 must treat all M2773/M2775 rows as source-only diagnostic inputs. It may
derive admission metadata from deltas, but it must not replace rows, resample
rows, run the backend, execute the actor, or select a winning intervention.

## Belief-Stress Admission Rows

M2779 should write one `belief_stress_admission_rows.csv` row per ordinary
candidate/intervention delta row and guarded context rows for mitigation
reference rows. Expected accounting:

```text
source delta rows: 96
ordinary delta rows: 72
mitigation reference delta rows: 24
candidate rows: 32
ordinary candidate rows: 24
mitigation reference candidate rows: 8
intervention conditions: 3
```

Recommended row schema:

```text
admission_row_id
candidate_id
role_family
dynamics_axis
seed
intervention_condition_id
ordinary_denominator_allowed
mitigation_reference
stress_family
belief_signal_class
road_departure_removed
road_departure_added
collision_changed
minimum_road_margin_m_delta
minimum_obstacle_clearance_m_delta
action_l1_mean
ego_response_l2_mean
command_response_proxy_delta
trace_delta_proxy_delta
admission_action
admission_reason
future_execution_allowed
future_training_allowed
requires_fresh_evidence
diagnostic_only
ranking_admissible
winner_selected
actor_visible_label
claim_boundary
```

The admitted `stress_family` values should be actor-invisible artifact labels:

```text
recurrent_hidden_reset_stress
previous_command_history_stress
held_actuator_history_stress
mitigation_reference_guard
```

The `belief_signal_class` should classify evidence without ranking:

```text
behavior_outcome_sensitive:
  road_departure_removed true or road_departure_added true or collision_changed
  true. This is still diagnostic and source-only.

action_response_sensitive:
  action_l1_mean or ego_response_l2_mean above the pack threshold, with no
  behavior outcome change.

trace_sensitive:
  trace_delta_proxy_delta or command_response_proxy_delta above the pack
  threshold, with weaker action/ego-response changes.

weak_or_context:
  below threshold, mitigation reference, or not suitable for future ordinary
  training admission.
```

The pack thresholds should be explicit, deterministic, and non-tuned:

```text
action_l1_mean_threshold: 0.03
ego_response_l2_mean_threshold: 0.10
command_response_proxy_abs_delta_threshold: 0.04
trace_delta_proxy_abs_delta_threshold: 1.0
```

These thresholds are materialization thresholds only. They are not performance
gates, ranking criteria, or proof of self-identification.

## Curriculum And Stress Buckets

M2779 should write `stress_curriculum_rows.csv` with actor-invisible buckets
for future materialization or training admission. Recommended fields:

```text
curriculum_row_id
stress_family
role_family
dynamics_axis
ordinary_candidate_count
mitigation_reference_count
behavior_outcome_sensitive_count
action_response_sensitive_count
trace_sensitive_count
weak_or_context_count
future_pack_priority
future_training_allowed
future_execution_allowed
requires_fresh_rollout
requires_training_manifest
ranking_admissible
claim_boundary
```

The curriculum should admit future work only if the row stays bounded:

```text
future materialization:
  allowed for all buckets that have complete ordinary accounting and actor
  guards.

future short training continuation:
  allowed only under a separate M2780+ manifest, after M2779 audit, and only as
  proposal generation. It must not be evidence of self-ID or promotion.

future fresh closed-loop execution:
  allowed only under a separate manifest that creates new rows, separates proof
  and generalization gates, and preserves the actor contract.
```

## Actor Contract

M2779 and any follow-up branch must preserve:

```text
P0 observation shape: 72
action shape: 3
deployed action mapping: steer, throttle, brake
actor input contract changed: false
actor input feature added: false
hidden/oracle actor input detected: false
role labels actor-visible: false
dynamics labels actor-visible: false
intervention labels actor-visible: false
stress labels actor-visible: false
curriculum labels actor-visible: false
admission labels actor-visible: false
outcome/progress/success/verdict labels actor-visible: false
```

Allowed deployable inputs remain ego response, actuator state, previous
physical commands, ego-frame road/free-space/obstacle geometry, and recurrent
or explicit command-response history. Forbidden inputs remain hidden dynamics
parameters, slip/tire-force shortcuts, TTC, reference trajectory, path error,
heading error, oracle feasibility, AEB/AES/drift labels, success/progress
labels, and precomputed answers.

## Claim And Route Boundaries

M2779 must preserve these boundaries:

```text
diagnostic_only: true
ranking_admissible: false
winner_selected: false
checkpoint_promoted: false
success_rate_verdict_computed: false
driver_performance_claim_made: false
paper_claim_made: false
finite_window_vs_gru_claim_made: false
current_sim_verdict_claim_made: false
high_fidelity_validation_claim_made: false
full_ideal_driver_claim_made: false
level3_self_id_claim_made: false
```

Route B remains separate. Any self-ID or finite-window-vs-GRU claim requires a
fair controller-family matrix, matched training budgets, source diversity, and
explicit L0/L1/L2/L3 comparison. M2778/M2779 do not provide that.

Route C remains separate. HF3 execution stays blocked until the source
dependency is resolved under the M2638 contract. M2778/M2779 do not provide
high-fidelity validation.

## Output Artifact Contract

M2779 should write:

```text
runs/m2779_engineering_controller_route_a_source_only_belief_stress_training_admission_pack_materialization/summary.json
runs/m2779_engineering_controller_route_a_source_only_belief_stress_training_admission_pack_materialization/belief_stress_admission_rows.csv
runs/m2779_engineering_controller_route_a_source_only_belief_stress_training_admission_pack_materialization/stress_curriculum_rows.csv
runs/m2779_engineering_controller_route_a_source_only_belief_stress_training_admission_pack_materialization/mitigation_reference_guard_rows.csv
runs/m2779_engineering_controller_route_a_source_only_belief_stress_training_admission_pack_materialization/actor_contract_guard_rows.csv
runs/m2779_engineering_controller_route_a_source_only_belief_stress_training_admission_pack_materialization/claim_boundary_rows.csv
runs/m2779_engineering_controller_route_a_source_only_belief_stress_training_admission_pack_materialization/gate_matrix.csv
runs/m2779_engineering_controller_route_a_source_only_belief_stress_training_admission_pack_materialization/run_state.json
docs/m2779-engineering-controller-route-a-source-only-belief-stress-training-admission-pack-materialization-preflight.md
experiments/manifests/m2780-engineering-controller-route-a-source-only-belief-stress-training-admission-pack-materialization-result-audit.json
```

M2779 should also write focused tests for the materializer:

```text
tests/test_engineering_controller_route_a_source_only_belief_stress_training_admission_pack_materialization.py
```

## Gate Matrix

M2779 passes only if all of these are true:

```text
M2778 design doc present
M2777 synthesis doc present
M2776 audit doc present
M2775 summary status_pass true
M2775 gate_matrix_pass true
M2773 summary status_pass true
M2773 gate_matrix_pass true
96 source delta rows loaded
72 ordinary delta rows accounted
24 mitigation reference delta rows guarded
32 source candidate rows loaded
admission row accounting complete
curriculum row accounting complete
mitigation reference rows guarded outside ordinary denominators
actor observation shape 72 preserved
action shape 3 preserved
hidden/oracle actor input detected false
actor-visible stress/admission/curriculum labels false
ranking admissible false
winner selected false
success-rate verdict computed false
new execution run false
training run false
PPO run false
paper/self-ID/high-fidelity claims false
M2780 follow-up audit manifest registered
```

## Negative Result Policy

If M2779 finds that M2775 deltas are too weak for a training/admission pack, it
must preserve that result and route to an audit or stop. It must not lower
self-ID gates, rank intervention modes, include mitigation rows in ordinary
denominators, or claim that the driver improved.

If M2779 finds incomplete row accounting, it must route to artifact repair.

If M2779 completes the pack, the only admitted next step is a result audit
before any materialization extension, fresh closed-loop execution, short
training continuation, or training-pack implementation.

## Follow-Up Decision

M2778 admits:

```text
m2779-engineering-controller-route-a-source-only-belief-stress-training-admission-pack-materialization-preflight
```

M2779 is a no-rollout infrastructure/materialization milestone. It may write a
new admission pack from existing artifacts, source code, focused tests, a
summary, milestone doc, gate matrix, and one M2780 result-audit manifest. It
must not execute the actor, train, validate, rank, promote, or claim driver
performance.

## Claim Boundary

Allowed M2778 claim:

```text
M2778 defines a bounded source-only belief-stress training/admission protocol
that can convert complete but modest M2775 diagnostic deltas into an auditable
M2779 admission-pack materialization before any training or fresh execution is
allowed.
```

Rejected claims:

```text
repair success
driver performance
validation readiness or result
controller-family ranking
intervention-condition ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```
