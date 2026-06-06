# M2844 Engineering Controller Route A Driver-Like Recurrent-Belief Architecture Training Redesign Protocol Result Audit

## Metadata

- status: completed
- audit decision: `accept_m2843_response_predictive_recurrent_belief_core_training_protocol_route_to_m2845_implementation_preflight_design`
- manifest: `experiments/manifests/m2844-engineering-controller-route-a-driver-like-recurrent-belief-architecture-training-redesign-protocol-result-audit.json`
- audit artifact: `docs/m2844-engineering-controller-route-a-driver-like-recurrent-belief-architecture-training-redesign-protocol-result-audit.md`
- parent protocol: `docs/m2843-engineering-controller-route-a-driver-like-recurrent-belief-architecture-training-redesign-protocol-design.md`
- parent audit: `docs/m2842-engineering-controller-route-a-post-hf3-stop-negative-evidence-architecture-redesign-or-freeze-result-audit.md`
- parent summary: `runs/m2838_engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_evidence_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2845-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-implementation-preflight-design.json`
- next: `m2845-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-implementation-preflight-design`

## Audit Decision

M2844 accepts M2843 as a concrete and claim-safe protocol design:

```text
accept_m2843_response_predictive_recurrent_belief_core_training_protocol_route_to_m2845_implementation_preflight_design
```

The acceptance is narrow. M2843 does not improve driver capability evidence by
itself and does not create a candidate checkpoint. It only admits a bounded
implementation-preflight design route because the protocol changes the evidence
axis away from same-surface diagnostics and actor-head-only repair.

Rejected immediate routes remain rejected:

```text
direct implementation without implementation-preflight design:
  rejected. The protocol still needs code/config artifact boundaries and exact
  proof/generalization/promotion row schemas before implementation.

actor_mean.bias-only continuation:
  rejected. M2843 explicitly requires recurrent/fusion or response-prediction
  parameter evidence and treats actor-head-only mutation as invalid.

same-surface M2838-like execution:
  rejected. M2838 is already complete and weak/negative.

direct Route C/HF3 retry:
  rejected. M2638/M2836 source dependency stop remains active.

direct Route B self-ID claim:
  rejected. No fair controller-family matrix or history-necessity proof has
  been run.
```

## Protocol Completeness Audit

M2844 audited M2843 against the required concrete protocol fields.

Architecture design is concrete:

```text
actor_encoder: human_view_online_gru
actor observation/action: 72 / 3
env history_length: 1
response stream: observation indices 0-11
context stream: observation indices 12-71
recurrent update: online GRUCell over response encoding
fusion: response belief, context encoding, and elementwise product
response_prediction_head: training-only
response_prediction_target_channels: observation indices 0-8
response_prediction_dim: 9
response_prediction_horizon: 4
response_prediction_stride: 1
```

Training recipe is concrete enough for an implementation-preflight design:

```text
source checkpoint: M2655
M2782 candidate checkpoint as new base: rejected
recurrent_sequence_training: required
response_prediction_aux_coef: required nonzero
baseline_action_anchor_checkpoint: M2655
max_updates: bounded preflight budget
checkpoint output: audit candidate only
active config overwrite: false
promotion metadata: false
```

Trainable parameter scope is materially different from actor-head-only repair:

```text
response_encoder
online_gru_cell
response_context_fusion
actor_mean
critic
log_std unless separately frozen
response_prediction_head
```

M2843 also requires a parameter-mutation trace and makes a candidate invalid if
only `actor_mean.bias` changes. This directly addresses the M2771 and M2782/M2786
guardrails.

## Actor And Label Boundary Audit

M2843 preserves the deployed actor contract:

```text
actor observation shape: 72
action shape: 3
hidden/oracle actor input required: false
wheel/slip branch required: false
privileged actor branch required: false
controller-mode branch required: false
actor-visible source labels: false
actor-visible stress-axis labels: false
actor-visible scenario-role labels: false
actor-visible route labels: false
actor-visible success/progress/verdict labels: false
```

The training-only response prediction target is limited to deployable
next-response channels from the 72-value observation stream:

```text
vx
vy
yaw_rate
ax
ay
steer_actuator
steer_rate
throttle_actuator
brake_actuator
```

It does not require `mu`, mass, tire stiffness, brake scale, actuator tau,
slip, tire force, oracle feasibility, scenario labels, TTC, required clearance,
oracle stopping distance, route decision labels, or success/progress/verdict
labels.

## Gate Separation Audit

M2843 separates the gates correctly:

```text
proof gates:
  actor 72/3 contract
  no actor-visible labels
  recurrent core mutation
  not actor-head-only
  live response prediction head
  hidden-response coupling diagnostics
  protected rows not washed out
  M2838 negative accounting visible

generalization gates:
  fresh task-source ids disjoint from recent Route A surfaces
  role coverage
  dynamics coverage
  multi-seed guard
  failure taxonomy retention
  current-sim not verdict
  source-only/current-sim separation

promotion gates:
  all proof gates passed
  generalization not regressed
  mitigation references preserved
  runtime budget audited
  no active config overwrite
  no winner without a promotion manifest
```

The separation is sufficient for M2845 to design an implementation preflight.
It is not sufficient to promote a checkpoint or claim self-identification.

## Negative Evidence Retention

M2843 retains M2838 as weak diagnostic evidence:

```text
selected rows: 16
resolved rows: 16
executed rows: 16
execution failures: 0
diagnostic success: 1
diagnostic collision: 2
diagnostic off_track: 13
```

M2843 does not compute a success-rate verdict from those rows. The rows may
guide evaluator-side admission priorities only; they are not actor-visible
labels, ordinary success denominators, or direct training targets.

## Accepted Follow-Up

M2844 routes to:

```text
m2845-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-implementation-preflight-design
```

M2845 must design the implementation preflight artifacts before code or
training. It should specify:

```text
1. exact code/config modules to touch;
2. response-prediction target extraction and row schemas;
3. trainable parameter group audit;
4. seed split and curriculum materialization protocol;
5. checkpoint manifest and parameter mutation trace requirements;
6. proof/generalization/promotion row schemas;
7. follow-up route to implementation preflight or branch stop.
```

If M2845 cannot define those implementation boundaries without changing actor
inputs or collapsing gates, the branch must route to freeze or stop rather than
train.

## Claim Boundary

Allowed M2844 claim:

```text
M2843 is accepted as a concrete claim-safe Route A response-predictive
recurrent-belief core training protocol design, and the branch may proceed to
M2845 implementation-preflight design.
```

Rejected claims:

```text
implementation_completed=false
training_completed=false
checkpoint_created=false
checkpoint_promoted=false
repair_success=false
recoverability_success=false
validation_readiness=false
validation_result=false
driver_performance=false
controller_family_ranking=false
winner_selection=false
success_rate_verdict=false
paper_evidence=false
finite_window_vs_gru_conclusion=false
current_sim_verdict=false
high_fidelity_validation=false
full_ideal_driver_completion=false
level3_self_identification=false
```
