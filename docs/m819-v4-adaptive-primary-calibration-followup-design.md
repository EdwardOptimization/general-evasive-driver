# M819 V4 Adaptive Primary Calibration Follow-Up Design

## Purpose

M819 designs the follow-up after M818 classified M817 as harness-positive but
near-identity.

The design question is:

```text
How should the next non-PPO probe distinguish useful adaptive residual
calibration from identity retention?
```

M819 is design-only:

```text
no implementation
no calibrator training run
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Starting Point

M817 established:

```text
split_valid: true
train rows: 57
holdout rows: 28
train normal collisions: 0
holdout normal collisions: 0
train intervention collision rate: 0.678363 -> 0.678363
holdout intervention collision rate: 0.702381 -> 0.702381
mean old-behavior action drift: 8.15e-7
max old-behavior action drift: 1.58e-6
actor checksum changed: false
M761 residual-head checksum changed: false
ppo_used: false
promoted: false
```

M818 audited this as:

```text
valid calibration harness
valid source-heldout retention gate
not a performance improvement
not meaningful adaptive gating
```

The next experiment must therefore add information, not simply repeat an
identity-gate pass.

## Frozen Contract

The next implementation admitted by this design must keep frozen:

```text
M568 actor
M761 residual head
actor observation contract
alpha base value = 0.2
primary margin threshold = 0.00005
train/holdout split unit = source_group_id + seed + fault_family_pair
```

Allowed trainable component, only after branch synthesis:

```text
a separate residual calibrator or fixed residual gate candidate
```

Forbidden:

```text
actor update
M761 residual-head update
PPO
checkpoint promotion
holdout-row optimization
oracle deploy-time inputs
threshold relaxation
```

## Candidate Families

The follow-up implementation should compare these families under the same
source-heldout exact evaluation.

### Family A: Identity Baseline

This is the M817 reference:

```text
gate = 0.999 or 1.0
action = base_action + 0.2 * gate * residual
```

Purpose:

```text
retention reference
not a useful calibration claim by itself
```

### Family B: Fixed Scalar Gate Grid

Evaluate feature-independent scalar gates:

```text
gate in [0.0, 0.25, 0.50, 0.75, 0.90, 0.95, 0.98, 0.999, 1.0]
```

Purpose:

```text
test whether simple residual suppression already improves normal margin
without washing out intervention sensitivity.
```

If a fixed scalar gate beats identity on train and holdout, the first
implementation should stay simple. A learned calibrator is unnecessary until a
fixed gate cannot explain the effect.

### Family C: Fixed Vector Gate Grid

Evaluate a small action-dimension grid:

```text
steer_gate in [0.0, 0.25, 0.50, 0.75, 1.0]
throttle_gate in [0.0, 0.50, 1.0]
brake_gate in [0.50, 0.75, 1.0]
```

Also include hand-picked probes tied to prior residual attribution:

```text
steer suppressed, brake retained
steer retained, brake retained
brake only
steer only
throttle zeroed
```

Purpose:

```text
separate useful brake residual retention from harmful steering residual drift.
```

This family should be evaluated before any learned vector gate so the learned
result has a simple fixed-gate baseline.

### Family D: Train-Only Adaptive Gate

Only if fixed scalar/vector gates expose a nontrivial Pareto frontier, train a
small adaptive gate on train rows only.

The adaptive gate may consume:

```text
frozen actor/residual features already available in the residual pathway
```

It must not consume:

```text
success
collision
margin
fault identity
source id
holdout labels
oracle deploy-time parameters
```

Recommended gate outputs:

```text
scalar_gate: one gate shared by all action residuals
vector_gate: steer/throttle/brake gates
template_gate: convex mixture over a small set of fixed-gate templates
```

The template-gate option is preferred if implementation cost is similar,
because it keeps learned behavior anchored to interpretable fixed-gate
candidates.

## Train-Only Selection Rule

The implementation should choose candidates using train rows only.

Lexicographic train filter:

```text
1. train normal collision_count == 0
2. train normal success_count == train rows
3. train intervention collision rate >= train baseline collision rate - 0.05
4. mean action drift <= 0.002 and max action drift <= 0.02
5. actor and M761 residual-head checksums unchanged
```

Then rank survivors by:

```text
primary: 5th-percentile normal margin lift over identity
secondary: mean normal margin lift over identity
tertiary: intervention collision-rate retention
quaternary: smaller action drift
```

The margin-lift metric is:

```text
calibrated_normal_margin - identity_normal_margin
```

Use identity, not the CSV margin, as the comparison baseline because M817
already showed exact replay is the relevant route.

## Holdout Acceptance Gate

Holdout rows are evaluation only.

A candidate selected on train rows may be called informative only if holdout
passes:

```text
holdout normal collision_count == 0
holdout normal success_count == holdout rows
holdout 5th-percentile normal margin lift >= 0.0
holdout mean normal margin lift >= 0.0
holdout intervention collision rate >= holdout baseline collision rate - 0.05
mean action drift <= 0.002
max action drift <= 0.02
actor checksum unchanged
M761 residual-head checksum unchanged
ppo_used == false
promoted == false
```

For a stronger candidate claim, require:

```text
holdout 5th-percentile normal margin lift >= 0.00001
or
holdout mean normal margin lift >= 0.00002
```

These are calibration-probe thresholds only. They are not promotion gates.

## Result Classes

The follow-up implementation should classify:

```text
v4_adaptive_primary_calibration_identity_only
v4_adaptive_primary_calibration_fixed_scalar_candidate
v4_adaptive_primary_calibration_fixed_vector_candidate
v4_adaptive_primary_calibration_adaptive_candidate
v4_adaptive_primary_calibration_train_only_overfit
v4_adaptive_primary_calibration_intervention_washout
v4_adaptive_primary_calibration_old_behavior_regression
v4_adaptive_primary_calibration_contract_violation
```

Interpretation:

```text
identity_only:
  retention works, but no nontrivial calibration evidence exists.

fixed_scalar_candidate:
  simple residual scaling explains the useful effect.

fixed_vector_candidate:
  action-component scaling is necessary and sufficient.

adaptive_candidate:
  learned source-conditioned gating beats fixed gates on holdout.

train_only_overfit:
  train lift fails to transfer to holdout.
```

## Required Outputs For Later Implementation

The later implementation should write:

```text
summary.json
candidate_grid.csv
train_candidate_metrics.csv
holdout_candidate_metrics.csv
intervention_candidate_metrics.csv
gate_summary.csv
selected_candidate.json
```

If an adaptive calibrator is trained, also write:

```text
calibrator.pt
training_metrics.csv
train_selection_rows.csv
holdout_exact_rows.csv
```

The calibrator artifact remains experiment-only. It is not a driver checkpoint.

## Failure Handling

If no fixed or adaptive candidate beats identity on holdout:

```text
classify as identity_only or train_only_overfit;
do not tune against holdout;
do not start PPO;
return to data or objective design.
```

If intervention collision sensitivity collapses:

```text
classify as intervention_washout;
prefer template gates that preserve rejected-history response;
do not accept a normal-margin-only candidate.
```

If only train rows improve:

```text
classify as objective_overfit;
rotate or expand source-heldout data before reusing the same holdout.
```

## Branch Synthesis Requirement

This branch has now accumulated the intended synthesis cadence since M810.
Therefore M819 must not route directly to implementation.

The next milestone is a process synthesis that decides whether to:

```text
continue into exact calibration-grid implementation;
pivot back to data generation;
stop the branch;
or promote the evidence into a new branch.
```

## Decision

Decision:

```text
adaptive_primary_calibration_followup_design_admit_branch_synthesis
```

Next blocker:

```text
m820-v4-low-margin-new-data-route-branch-synthesis
```
