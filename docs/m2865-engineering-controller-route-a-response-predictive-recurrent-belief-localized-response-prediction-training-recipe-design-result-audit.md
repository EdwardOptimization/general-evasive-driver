# M2865 Engineering Controller Route A Response-Predictive Recurrent-Belief Localized Response-Prediction Training Recipe Design Result Audit

## Metadata

- status: completed
- decision: `accept_m2864_recipe_design_route_to_m2866_implementation_preflight`
- manifest: `experiments/manifests/m2865-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-recipe-design-result-audit.json`
- audit artifact: `docs/m2865-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-recipe-design-result-audit.md`
- parent design: `docs/m2864-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-recipe-design.md`
- parent synthesis: `docs/m2863-engineering-controller-route-a-response-predictive-recurrent-belief-response-prediction-localization-branch-synthesis.md`
- parent summary: `runs/m2861_engineering_controller_route_a_response_predictive_recurrent_belief_response_prediction_trace_localization_materialization/summary.json`
- follow-up manifest: `experiments/manifests/m2866-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-implementation-preflight.json`
- next: `m2866-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-implementation-preflight`

## Audit Decision

M2865 accepts M2864 as a complete claim-safe design for a bounded localized
response-prediction implementation preflight:

```text
accept_m2864_recipe_design_route_to_m2866_implementation_preflight
```

The acceptance is narrow. M2864 is specific enough to constrain an
implementation preflight, but it is not training evidence, validation evidence,
driver-performance evidence, paper evidence, current-sim verdict evidence,
high-fidelity evidence, full-driver evidence, or self-identification evidence.

M2865 itself does not run reset, step, rollout, replay, training, PPO,
validation, ranking, winner selection, promotion, success-rate verdict
computation, or performance evaluation.

## Design Completeness Audit

M2864 defines the required recipe boundaries:

```text
target dimension: 9
target horizon: 4
target channels: vx_norm vy_norm yaw_rate_norm ax_norm ay_norm
                 steer_actuator_norm steer_rate_norm throttle_actuator
                 brake_actuator
loss form: valid-mask-weighted bounded response-prediction loss
loss-mass normalization: required
terminal/unavailable targets: masked out
future labels actor-visible: false
actor observation shape: 72 unchanged
deployed action shape: 3 unchanged
```

M2864 also defines a bounded initial weight table. The table is modest,
pre-registered, and cannot be tuned after observing closed-loop outcomes:

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
all other valid entries: 1.00 before normalization
allowed normalized weight range: [0.75, 1.50]
```

## M2861 Signal Audit

M2864 correctly maps the M2861 signals without rebranding them as performance:

```text
actuator_response_prediction_loss_weight_review: 155 localized rows
ego_response_prediction_loss_weight_review: 134 localized rows
horizon_boundary_masking_preserved: 863 localized rows
```

M2864 explicitly notes that the recipe-signal valid and gap counts are
channel-localized aggregates and must not be compared directly against the
vector-level M2859 trace row count. M2865 accepts this guard.

## Public-Row Overfit Audit

M2864 keeps M2850-derived rows as explanatory public diagnostic rows only.
Future M2866 implementation must include:

```text
M2850 explanatory surface:
  proof and guardrail only
  not training target selection
  not ranking
  not validation
  not promotion

fresh/disjoint response-prediction surface:
  minimum 8 rows
  source-diverse and disjoint from M2850 when available
  reported separately from public explanatory rows
```

M2865 rejects any interpretation where M2866 optimizes only fixed public M2850
rows or treats those rows as ordinary success denominators.

## Rollback Gate Audit

M2864 defines rollback gates that are adequate for an implementation preflight:

```text
actor input shape change -> rollback
future-label actor visibility -> rollback
valid-target mask or terminal-gap accounting regression -> rollback
public-only improvement with fresh/disjoint worsening -> rollback
response-prediction loss improvement with clearance/progress or low-speed
telemetry washout -> rollback
```

M2866 must materialize machine-readable rows for those gates before its result
can be interpreted.

## Actor And Claim Boundary

M2865 accepts that M2864 preserves:

```text
actor observation shape: 72
action shape: 3
future response labels actor-visible: false
hidden/oracle actor input required: false
ordinary success denominator allowed for public rows: false
ranking admissible for public rows: false
checkpoint promotion admitted: false
```

M2866 may run bounded training only as an implementation preflight. It must not
rank checkpoints, select a winner, promote a checkpoint, compute success-rate
verdicts, or claim repair success, driver performance, validation readiness,
paper evidence, current-sim verdict, high-fidelity validation, full-driver
completion, or level3 self-identification.

## Follow-Up Route

M2865 registers M2866:

```text
m2866-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-implementation-preflight
```

M2866 should implement and execute a bounded localized response-prediction
training implementation preflight. It should write response-loss weight rows,
valid-target mask accounting rows, public/fresh surface accounting rows,
rollback gate rows, actor/claim guard rows, parameter trace rows, summary,
run-state, and a result-audit manifest. If implementation cannot preserve the
actor contract or fresh-surface boundary, it should fail closed and route to
result audit or repair rather than weakening gates.

## Rejected Shortcuts

M2865 rejects:

```text
direct PPO continuation without M2866 preflight artifacts
post-hoc weight tuning on M2850 public rows
public-row-only optimization
ranking from response-prediction loss
promotion from auxiliary-loss improvement
validation or performance claims
paper, current-sim, high-fidelity, full-driver, or self-ID claims
```
