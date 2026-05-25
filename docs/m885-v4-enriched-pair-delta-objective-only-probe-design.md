# M885 V4 Enriched Pair-Delta Objective-Only Probe Design

## Purpose

M885 designs the first no-PPO objective-only probe after the M884 branch
synthesis.

The design question is:

```text
Can a small actor-coupling update improve the M883 exact pair-delta objective
without immediately creating objective overfit or proof washout?
```

M885 is design-only:

```text
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## Update Scope

M886 may train only a narrow actor-coupling scope:

```text
actor mean / coupling parameters already used by existing actor-coupling
objective tools.
```

M886 must not train:

```text
M761 residual head
critic-only parameters as an independent objective
environment or simulator parameters
actor input contract
PPO rollout machinery
```

If the existing train-scope helper cannot isolate the intended scope, M886 must
stop and route to train-scope audit instead of updating.

## Objective

Primary objective:

```text
M883 enriched pair-delta improvement/degradation preference loss.
```

For `pair_delta_improvement` rows:

```text
prefer first_override_action over normal_action under the same normal
observation/recurrent hidden state.
```

For `pair_delta_degradation` rows:

```text
prefer normal_action over harmful first_override_action under the same normal
observation/recurrent hidden state.
```

M886 must report weighted and unweighted losses per split:

```text
objective_train_public
objective_eval_public
source_holdout_public
new_signature_holdout_public
```

## Trust Region

The raw update should be deliberately small:

```text
optimizer: Adam
learning_rate: 1e-6 to 5e-6
steps: 32 to 64
grad_clip_norm: 0.5
parameter_l2_anchor_to_base: enabled
action_mean_anchor_on_all_m883_rows: enabled
```

M886 must write:

```text
raw_candidate checkpoint
interpolation candidates between base and raw
exact objective metrics for every candidate
parameter delta metrics
action drift metrics on M883 rows
```

## Interpolation

M886 must not accept the raw candidate directly.

Interpolation grid:

```text
alpha = 0.0
alpha = 0.001
alpha = 0.0025
alpha = 0.005
alpha = 0.01
alpha = 0.02
alpha = 0.05
alpha = 0.10
```

If all nonzero alphas regress exact holdout metrics, the probe is rejected and
the branch routes to objective redesign or data expansion.

## Exact Gates

M886 is a probe, not a promotion path. It may produce candidates but cannot
promote them.

A candidate is exact-admissible only if:

```text
train objective_loss_mean improves vs base
eval objective_loss_mean does not regress beyond tolerance
source_holdout objective_loss_mean does not regress beyond tolerance
new_signature_holdout objective_loss_mean does not regress beyond tolerance
all exact losses finite
actor input contract unchanged
M761 residual head unchanged
PPO not used
```

Suggested tolerance:

```text
exact_holdout_regression_tolerance: 1e-4
```

## Replay And Behavior Retention

M886 should not run full promotion replay gates. That should be a later audit if
exact-admissible candidates exist.

However, M886 must precompute a retention plan:

```text
old replay/proof surfaces used by the current branch
M877/M880 pair-delta rows as exact objective surfaces
behavior seeds used by current public gate stack
protected public proof rows from prior branches
```

M887, if admitted, should decide which exact-admissible candidate deserves
replay/behavior gate evaluation.

## Rejection Rules

Reject the probe if any of these happen:

```text
raw update changes actor input contract
residual head changes
all nonzero interpolation alphas regress exact holdout metrics
train improves only by making degradation holdouts worse
parameter or action drift is large relative to M883 action-target scale
loss improvements require tuning against source_holdout or new_signature_holdout
```

## Required Artifacts

M886 should write:

```text
src/autodrift/v4_enriched_pair_delta_objective_only_probe.py
tests/test_v4_enriched_pair_delta_objective_only_probe.py
runs/m886_v4_enriched_pair_delta_objective_only_probe/summary.json
runs/m886_v4_enriched_pair_delta_objective_only_probe/candidate_metrics.csv
runs/m886_v4_enriched_pair_delta_objective_only_probe/interpolation_metrics.csv
runs/m886_v4_enriched_pair_delta_objective_only_probe/exact_objective_by_split.csv
runs/m886_v4_enriched_pair_delta_objective_only_probe/action_drift_metrics.csv
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt
docs/m886-v4-enriched-pair-delta-objective-only-probe-implementation.md
```

## Decision

Decision:

```text
enriched_pair_delta_objective_only_probe_design_admit_m886
```

Next:

```text
m886-v4-enriched-pair-delta-objective-only-probe-implementation
```

M886 may run a small objective-only actor-coupling update, but must not run PPO
or promote a checkpoint.
