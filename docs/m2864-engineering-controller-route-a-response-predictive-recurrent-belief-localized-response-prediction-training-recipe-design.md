# M2864 Engineering Controller Route A Response-Predictive Recurrent-Belief Localized Response-Prediction Training Recipe Design

## Metadata

- status: completed
- decision: `admit_m2865_localized_response_prediction_training_recipe_design_result_audit`
- manifest: `experiments/manifests/m2864-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-recipe-design.json`
- design artifact: `docs/m2864-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-recipe-design.md`
- parent synthesis: `docs/m2863-engineering-controller-route-a-response-predictive-recurrent-belief-response-prediction-localization-branch-synthesis.md`
- parent summary: `runs/m2861_engineering_controller_route_a_response_predictive_recurrent_belief_response_prediction_trace_localization_materialization/summary.json`
- parent recipe signals: `runs/m2861_engineering_controller_route_a_response_predictive_recurrent_belief_response_prediction_trace_localization_materialization/response_prediction_recipe_signal_rows.csv`
- follow-up manifest: `experiments/manifests/m2865-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-recipe-design-result-audit.json`
- next: `m2865-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-recipe-design-result-audit`

## Design Decision

M2864 admits a bounded result audit of this localized response-prediction
training-recipe design. It does not admit direct PPO continuation.

The later implementation preflight, if M2865 accepts this design, may only
change the training-side response-prediction auxiliary loss and its audit
instrumentation. It must not change actor observations, deployed action shape,
reward semantics, environment dynamics, sampler rows, checkpoint ranking,
promotion rules, or validation denominators.

M2864 itself does not run reset, step, rollout, replay, training, PPO,
validation, ranking, winner selection, checkpoint promotion, success-rate
verdict computation, driver-performance evaluation, paper evaluation,
current-sim verdict, high-fidelity validation, full-driver gate, or
self-identification test.

## Evidence Used

M2863 accepted M2843-M2862 as complete but diagnostic Route A evidence and
continued only to bounded design.

M2861 materialized:

```text
response-prediction localization rows: 1152
channel summary rows: 36
recipe signal rows: 3
localized pairs: 16
localized subject rows: 32
relative high-error rows: 289
terminal gap accounted rows: 863
```

M2861 recipe signals:

```text
actuator_response_prediction_loss_weight_review: 155 localized rows
ego_response_prediction_loss_weight_review: 134 localized rows
horizon_boundary_masking_preserved: 863 localized rows
```

Channel/horizon high-error concentrations from M2861:

```text
h1 ax_norm and ay_norm: ego-response loss review
h1 brake_actuator: actuator loss review
h2 ax_norm: ego-response loss review
h2 steer_actuator_norm and brake_actuator: actuator loss review
h3 yaw_rate_norm: ego-response loss review
h3 brake_actuator: actuator loss review
h4 yaw_rate_norm: ego-response loss review
h4 brake_actuator: actuator loss review
```

The recipe-signal valid and gap counts are channel-localized aggregates. They
must not be compared directly against the vector-level M2859 trace row count.

## Route Boundary

This remains Route A engineering-controller work under
`docs/post-m2470-route-plan.md`.

Allowed Route A interpretation:

```text
a deployable actuator-level controller recipe may target training-side
response prediction while preserving the human-view actor contract
```

Forbidden interpretation:

```text
driver performance
checkpoint superiority
repair success
validation readiness or validation result
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation
full ideal driver completion
level3 self-identification
```

## Training-Side Loss Contract

A future implementation preflight may implement only this bounded auxiliary
loss form:

```text
loss_response =
  sum_{t,h,c}(valid_mask[t,h,c] * normalized_weight[h,c] *
             huber(predicted_response[t,h,c] - target_response[t,h,c]))
  / max(epsilon, sum_{t,h,c}(valid_mask[t,h,c] * normalized_weight[h,c]))
```

Required properties:

```text
target dimension: 9
target horizon: 4
target channels: vx_norm vy_norm yaw_rate_norm ax_norm ay_norm
                 steer_actuator_norm steer_rate_norm throttle_actuator
                 brake_actuator
loss type: bounded Huber or existing bounded response-prediction loss
valid_mask source: runtime target availability only
terminal/unavailable targets: mask to zero
missing targets: never impute
future labels: training/evaluator only and never actor-visible
loss-mass normalization: required so weighting does not silently raise the
                         total auxiliary loss scale
actor observation shape: 72 unchanged
deployed action shape: 3 unchanged
```

## Initial Weight Table

The implementation preflight must pre-register the following initial table and
must not tune it after observing closed-loop success outcomes.

Base weight:

```text
all valid response channels: 1.00
allowed weight range after normalization: [0.75, 1.50]
zeroing a valid channel: forbidden
```

Localized boosts before normalization:

```text
h1 ax_norm: 1.25
h1 ay_norm: 1.25
h1 brake_actuator: 1.35

h2 ax_norm: 1.20
h2 steer_actuator_norm: 1.20
h2 brake_actuator: 1.35

h3 yaw_rate_norm: 1.20
h3 brake_actuator: 1.35

h4 yaw_rate_norm: 1.20
h4 brake_actuator: 1.35
```

All other valid channel/horizon entries remain at 1.00 before normalization.

The table is intentionally modest. M2861 localized response-prediction errors
on public diagnostic rows, so this design rejects a large weight sweep or
post-hoc public-row fitting.

## Horizon Masking Requirement

The `horizon_boundary_masking_preserved` signal is treated as a hard contract,
not as an objective to optimize.

Future implementation must write audit rows proving:

```text
target_available=false rows do not contribute loss
terminal horizon gaps are counted
terminal horizon gaps are not converted to zero targets
gap counts are compared to M2859/M2861 accounting
no no_valid_targets row is used for ranking or promotion
```

## Public-Row Overfit Guards

M2861 rows are M2850-derived public diagnostic rows. Future implementation may
use them only as explanatory proof rows for schema and regression checks.

The implementation preflight must include at least two surfaces:

```text
M2850 explanatory surface:
  purpose: preserve and explain the existing diagnostic evidence
  allowed use: proof and guardrail only
  forbidden use: training target selection ranking validation promotion

fresh/disjoint response-prediction surface:
  purpose: detect public-row overfit and response-prediction washout
  selection: source-diverse rows disjoint from M2850 when available
  minimum: 8 rows with baseline and candidate/recipe subjects
  forbidden use: checkpoint promotion unless a later promotion manifest exists
```

If a fresh/disjoint surface cannot be formed, the implementation preflight must
fail closed or route to artifact repair. It must not optimize only fixed M2850
rows.

## Rollback And Audit Gates

A future implementation preflight must define rollback criteria before training
starts.

Proof gates:

```text
response-prediction loss table exactly matches this design
actor observation/action contract unchanged
future labels actor-visible false
horizon mask accounting preserved
M2861 localization artifacts remain unchanged
```

Generalization gates:

```text
fresh/disjoint surface written
fresh/disjoint response-prediction diagnostics finite
public M2850 explanatory rows and fresh rows reported separately
no fresh-surface washout of clearance/progress/low-speed telemetry buckets
```

Rollback gates:

```text
rollback if actor input shape changes
rollback if future labels become actor-visible
rollback if valid target masking or terminal gap accounting regresses
rollback if public explanatory rows improve but fresh/disjoint rows worsen
rollback if response-prediction loss improves while clearance/progress or
low-speed telemetry buckets worsen on the audit surface
```

Promotion gates:

```text
not admitted by this design
checkpoint_promoted=false
winner_selected=false
success_rate_verdict_computed=false
```

## Follow-Up Route

M2864 registers:

```text
m2865-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-recipe-design-result-audit
```

M2865 should audit this design before any implementation preflight. It should
accept the route only if the loss weighting, horizon masking, public-row
overfit guards, fresh-surface requirements, rollback gates, actor contract, and
claim boundary are complete. If accepted, M2865 may register a bounded M2866
implementation preflight. If rejected, it should route to design repair,
instrumentation repair, branch synthesis, or stop.

## Claim Boundary

Allowed M2864 claim:

```text
M2864 defines a bounded localized response-prediction training recipe design
and registers M2865 result audit.
```

Rejected claims:

```text
training_run=false
ppo_used=false
validation_run=false
ranking_run=false
winner_selected=false
checkpoint_promoted=false
success_rate_verdict_computed=false
repair_success_claim_made=false
driver_performance_claim_made=false
paper_claim_made=false
current_sim_verdict_claim_made=false
high_fidelity_validation_claim_made=false
full_ideal_driver_gate_passed=false
level3_self_id_claim_made=false
```
