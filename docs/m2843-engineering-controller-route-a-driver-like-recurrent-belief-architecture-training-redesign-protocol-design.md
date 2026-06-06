# M2843 Engineering Controller Route A Driver-Like Recurrent-Belief Architecture Training Redesign Protocol Design

## Metadata

- status: completed
- decision: `admit_response_predictive_recurrent_belief_core_training_protocol_route_to_m2844_audit`
- manifest: `experiments/manifests/m2843-engineering-controller-route-a-driver-like-recurrent-belief-architecture-training-redesign-protocol-design.json`
- design artifact: `docs/m2843-engineering-controller-route-a-driver-like-recurrent-belief-architecture-training-redesign-protocol-design.md`
- parent audit: `docs/m2842-engineering-controller-route-a-post-hf3-stop-negative-evidence-architecture-redesign-or-freeze-result-audit.md`
- route plan: `docs/post-m2470-route-plan.md`
- observation contract: `docs/observation-contract.md`
- source checkpoint: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt`
- follow-up manifest: `experiments/manifests/m2844-engineering-controller-route-a-driver-like-recurrent-belief-architecture-training-redesign-protocol-result-audit.json`
- next: `m2844-engineering-controller-route-a-driver-like-recurrent-belief-architecture-training-redesign-protocol-result-audit`

## Protocol Decision

M2843 admits a bounded Route A recurrent-belief architecture/training redesign
protocol:

```text
response_predictive_recurrent_belief_core_training_protocol
```

This is a protocol design only. It does not implement the protocol, train,
reset, step, roll out, replay, validate, rank, select a winner, promote a
checkpoint, compute a success-rate verdict, or claim driver performance.

The protocol is designed to be materially different from the rejected scalar
actor-head repair loop:

```text
rejected repeat:
  actor_mean.bias-only repair or continuation

admitted redesign:
  train and audit the recurrent response-belief core, response/context fusion,
  actor head, critic, and a self-supervised next-response prediction head under
  the unchanged 72-value human-view actor input contract
```

The immediate follow-up is M2844 protocol result audit. Only if M2844 accepts
this design should a later implementation preflight create code/config
artifacts for the training branch.

## Evidence Used

M2843 uses the current negative and bounded Route A evidence as route-control
input, not as performance proof:

```text
M2838 diagnostic accounting:
  fixed selected rows: 16
  resolved rows: 16
  executed rows: 16
  execution failure rows: 0
  diagnostic success: 1
  diagnostic collision: 2
  diagnostic off_track: 13

M2840/M2841/M2842:
  same-surface execution loop rejected
  immediate limited-baseline freeze rejected as the first next route
  scalar actor-head bias repeat rejected
  Route C/HF3 retry blocked by M2638/M2836 source dependency boundary
  direct Route B self-ID claim blocked until a fair controller-family matrix

M2771:
  actor-head bias repair family completed with negative diagnostic evidence

M2782/M2786:
  belief-stress short training produced a bounded candidate and small diagnostic
  deltas, but the recorded update method and trainable parameters remained
  actor_mean.bias-only and are therefore not sufficient as the new redesign
```

The post-M2470 route plan remains binding: Route A may pursue an engineering
controller baseline, but current-sim diagnostics cannot become the whole loop
and cannot be upgraded into paper, current-sim, high-fidelity, or full-driver
verdicts.

## Actor And Runtime Contract

The redesign keeps the deployed actor input/output contract unchanged:

```text
actor observation shape: 72
action shape: 3
actor_encoder family: human_view_online_gru
env history_length: 1
action_history_mode: full
road_lookahead_count: 8
obstacle_slots: 4
wheel_observation_mode: none
include_privileged_params: false
deployed action: [steer_command, throttle_command, brake_command]
```

Allowed actor-visible inputs remain only:

```text
ego kinematics and IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road/free-space boundary geometry
ego-frame obstacle geometry and relative motion
online recurrent hidden state produced from past deployable observations
```

Forbidden actor-visible inputs remain forbidden:

```text
mu mass tire stiffness brake scale actuator tau slip tire force
oracle feasibility AEB/AES/drift labels controller mode
speed_ref beta_target path error heading error path curvature
TTC required clearance oracle stopping distance
source stress-axis scenario-role route success progress or verdict labels
```

Auxiliary targets may use only deployable next-frame response channels derived
from the same observation stream. Hidden dynamics labels, scenario role labels,
success labels, and feasibility labels are not valid auxiliary targets for this
Route A driver redesign.

## Architecture Protocol

The first implementation preflight should use the existing 72-value
`human_view_online_gru` actor family and add a training-only next-response
prediction head. It should not introduce a new actor input shape.

Required architecture settings:

```text
actor_encoder: human_view_online_gru
hidden_size: 128 unless a separate audited compatibility design changes it
response stream: observation indices 0-11
context stream: observation indices 12-71
recurrent update: online GRUCell over response encoding
fusion: recurrent response belief, context encoding, and elementwise product
response_prediction_head: enabled for training only
response_prediction_target_channels: observation indices 0-8
response_prediction_dim: 9
response_prediction_horizon: 4
response_prediction_stride: 1
```

The response prediction target is:

```text
vx vy yaw_rate ax ay steer_actuator steer_rate throttle_actuator brake_actuator
```

It intentionally excludes hidden dynamics and excludes previous command fields
because future commands are supplied to the prediction head as actions during
training.

Required trainable parameter groups:

```text
response_encoder
online_gru_cell
response_context_fusion
actor_mean
critic
log_std unless frozen by a separate config guard
response_prediction_head
```

Forbidden as the main redesign:

```text
actor_mean.bias-only update
actor_mean-only update
hidden/oracle feature branch
wheel/slip branch
privileged_human_view_online_gru
controller-mode-conditioned branch
rule switch or route classifier
```

The implementation preflight must write a parameter-mutation trace. A candidate
from this branch is invalid if all non-actor-head recurrent/fusion parameters
remain unchanged.

## Training Recipe Protocol

The source checkpoint should be M2655, not the M2782 actor-head continuation
candidate:

```text
source_checkpoint:
  runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt
```

M2782/M2786 may supply curriculum and gate lessons, but not the candidate
checkpoint as the new base.

The first training implementation should be a bounded short-training preflight,
not a promotion attempt:

```text
recurrent_sequence_training: true
response_prediction_aux_coef: enabled and nonzero
response_prediction_dim: 9
response_prediction_horizon: 4
response_prediction_stride: 1
baseline_action_anchor_checkpoint: M2655 source checkpoint
baseline_action_anchor_coef: enabled at a small preservation weight
trainable groups: recurrent belief core plus actor/critic heads
max_updates: small bounded preflight budget
checkpoint output: candidate artifact for audit only
active config overwrite: false
promotion metadata: false
```

The training curriculum should combine:

```text
source-only role families:
  stable_avoidable
  stable_aes
  drift_required_recovery
  unavoidable_mitigation if currently supported by the source-only fixture

dynamics axes:
  nominal_or_role_default
  fault_delay_noise
  friction/mass/brake/steer-delay variation only if represented as evaluator
  metadata and not actor input

stress axes:
  previous_command_history_stress
  held_actuator_history_stress
  recurrent_hidden_reset_stress
  offtrack_containment_negative_rows
  collision_mitigation_negative_rows
```

M2838 rows may influence evaluator-side admission priorities, but they must not
be used as actor-visible labels, ordinary success denominators, or direct
performance targets.

Required split discipline:

```text
train seeds: disjoint from proof and generalization seeds
proof seeds: small fixed panel for mechanism gates
generalization seeds: fresh heldout panel disjoint from prior Route A surfaces
prior protected surfaces: excluded or guardrail-only
HF3 blocker rows: guardrail-only
single-seed verdicts: forbidden
```

## Proof Gates

Proof gates test whether the redesign changed the intended mechanism, not
whether the driver is good.

Required proof gates:

```text
proof_actor_contract_72_3:
  every candidate artifact reports observation 72 action 3 no hidden/oracle
  actor input

proof_no_actor_visible_labels:
  source stress-axis scenario-role route outcome success progress and verdict
  labels remain evaluator metadata only

proof_recurrent_core_mutated:
  response_encoder online_gru_cell response_context_fusion or response
  prediction head has finite nonzero delta from the source state

proof_not_actor_head_only:
  candidate is invalid if actor_mean.bias is the only changed parameter group

proof_response_prediction_head_live:
  response prediction head exists and produces finite next-response predictions
  over heldout proof sequences

proof_hidden_response_coupling:
  normal recurrent hidden, reset-hidden, zero-history, and wrong-history
  evaluator interventions are recorded as proof diagnostics, with labels hidden
  from actor input

proof_protected_rows_not_washed_out:
  mitigation reference rows, prior-surface protected rows, and HF3 blocker rows
  remain outside ordinary denominators

proof_m2838_negative_accounting_visible:
  M2838 remains 1 success, 2 collision, 13 off_track diagnostic evidence only
```

These proof gates cannot by themselves promote a checkpoint or establish
self-identification.

## Generalization Gates

Generalization gates test whether the mechanism survives fresh surfaces without
public-surface overfit.

Required generalization gates:

```text
generalization_fresh_task_source_ids:
  evaluation rows are disjoint from M2737 M2759 M2807 M2816 M2828 and M2838
  fixed task-source ids

generalization_role_coverage:
  stable_avoidable stable_aes drift_required_recovery and any supported
  mitigation role appear in the heldout panel

generalization_dynamics_coverage:
  nominal fault_delay_noise and unseen dynamics-range buckets are represented
  as evaluator-side metadata

generalization_multi_seed:
  no single seed or single row can pass the gate alone

generalization_failure_taxonomy_retained:
  off_track collision speed_too_low and mitigation failures remain separate
  rows and are not collapsed into a single success-rate story

generalization_current_sim_not_verdict:
  current-sim rows remain diagnostic and do not become a current-sim verdict

generalization_source_only_separation:
  source-only/HF0 evidence and current-sim evidence are reported separately
```

## Promotion Gates

Promotion is explicitly out of scope for M2843 and for the first implementation
preflight. A later promotion manifest may exist only after proof and
generalization audits pass.

Minimum future promotion guards:

```text
promotion_all_proof_gates_passed:
  no failed proof gate hidden by aggregate metrics

promotion_generalization_not_regressed:
  heldout failure taxonomy does not regress on protected offtrack collision or
  mitigation rows

promotion_mitigation_reference_preserved:
  protected mitigation component rows do not wash out

promotion_runtime_budget_audited:
  inference/runtime report exists for the candidate

promotion_no_active_config_overwrite:
  candidate is not installed as the active baseline by the training preflight

promotion_no_winner_without_manifest:
  no winner selection or checkpoint replacement before a dedicated promotion
  manifest and audit
```

## Required Future Artifacts

If M2844 accepts this protocol, the first implementation preflight should write:

```text
protocol_config_snapshot.json
trainable_parameter_groups.csv
training_curriculum_rows.csv
seed_split_rows.csv
training_run_rows.csv
checkpoint_manifest.json
parameter_mutation_trace.csv
response_prediction_probe_rows.csv
hidden_intervention_probe_rows.csv
proof_gate_rows.csv
generalization_gate_rows.csv
promotion_guard_rows.csv
actor_contract_guard_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
summary.json
follow_up_manifest.json
```

The summary must include explicit false flags for:

```text
repair_success
driver_performance
validation_readiness
validation_result
controller_family_ranking
source_family_ranking
task_family_ranking
profile_ranking
stress_axis_ranking
scenario_role_ranking
winner_selection
checkpoint_promotion
success_rate_verdict
paper_evidence
finite_window_vs_gru_conclusion
current_sim_verdict
high_fidelity_validation
full_ideal_driver_completion
level3_self_identification
```

## Follow-Up Route

M2843 routes to:

```text
m2844-engineering-controller-route-a-driver-like-recurrent-belief-architecture-training-redesign-protocol-result-audit
```

M2844 must audit this protocol before implementation. If M2844 accepts it, the
next admitted route should be a bounded implementation preflight design for the
response-predictive recurrent-belief core training branch. If M2844 rejects it,
the branch should route to limited-baseline freeze or explicit stop rather than
repeat actor-head repair or same-surface M2838 execution.

## Claim Boundary

Allowed M2843 claim:

```text
M2843 defines a concrete bounded protocol for a materially different Route A
recurrent-belief architecture/training branch under the unchanged actor
72/action 3 no-hidden/no-oracle contract and routes it to M2844 audit.
```

Rejected claims:

```text
repair_success=false
recoverability_success=false
validation_readiness=false
validation_result=false
driver_performance=false
controller_family_ranking=false
winner_selection=false
checkpoint_promotion=false
success_rate_verdict=false
paper_evidence=false
finite_window_vs_gru_conclusion=false
current_sim_verdict=false
high_fidelity_validation=false
full_ideal_driver_completion=false
level3_self_identification=false
```
