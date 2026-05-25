# M784 V4 Normal-Margin-Aware Residual Calibration Audit

## Purpose

M784 audits the M783 normal-margin-aware calibrator result before any further
calibration, replay, PPO, or checkpoint promotion.

The question is:

```text
Did the first gate-only calibration repair the M780 boundary without losing the
self-ID residual signal?
```

This milestone is audit-only:

```text
no replay run
no calibrator retraining
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Evidence Summary

M783 result:

```text
result_class: v4_normal_margin_calibration_no_gap_lift

positive_rows: 2652
supported_positive_rows: 2640
reconstructed_rows: 2640
sample_reconstruction_success_rate: 0.995475
metadata_missing_rows: 0
rejected_rows: 12

candidate_alpha_count: 0
candidate_alphas: []

actor_backbone_changed: false
base_residual_head_changed: false
optimizer_updates_only_calibrator: true
ppo_used: false
promoted: false
```

This is a clean implementation result:

```text
tooling works
checksums are preserved
only calibrator parameters are trained
the run writes full replay/objective artifacts
```

It is not a candidate because no alpha passes the intervention-gap gate.

## Normal Retention Result

M783 fixed the active normal-boundary failure:

```text
alpha 0.125:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  active_source_min_margin: +0.000067

alpha 0.15:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  active_source_min_margin: +0.000056

alpha 0.2:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  active_source_min_margin: +0.000033
```

Compared with M780:

```text
M780 alpha 0.125 active source margin: +0.000009
M780 alpha 0.15 active source margin:  -0.000014
M780 alpha 0.2 active source margin:   -0.000062
```

So the normal-margin suppression did what it was designed to do.

## Intervention Signal Result

M783 did not retain enough intervention separation:

```text
base alpha 0.0 intervention gap mean/p10:
  0.040348 / 0.025782

M783 alpha 0.125:
  0.042183 / 0.026313
  closed_loop_gap_pass: false

M783 alpha 0.15:
  0.042554 / 0.026420
  closed_loop_gap_pass: false

M783 alpha 0.2:
  0.043298 / 0.026634
  closed_loop_gap_pass: false
```

At alpha `0.2`, the mean gap lift is:

```text
0.043298 - 0.040348 = 0.002950
```

The gate requires at least `+0.003`, so the result misses by about `5e-5`.
That near-miss is still a fail. The workflow should not weaken the gate after
seeing the result.

## Calibrator Behavior

Final gate metrics:

```text
gate_normal_mean: 0.499727
gate_intervention_mean: 0.499986
active normal gate: about 0.499707
active intervention gate: about 0.499795 to 0.500010
```

Interpretation:

```text
The calibrator learned almost global half-scaling.
```

This explains both sides of the result:

```text
normal retention improves because every residual is roughly halved;
intervention signal weakens because every intervention residual is also roughly
halved.
```

The first calibration objective did not create a useful context-dependent
belief/action gate.

## Supported Claims

M784 supports:

```text
1. Normal-margin-aware calibration is a valid tooling path: it can protect the
   active near-boundary normal source without mutating actor or residual head.

2. The first scalar gate objective is not sufficient: it behaves like global
   alpha reduction and fails intervention signal retention.

3. More of the same training is unlikely to be the right next move; the
   objective needs a stronger asymmetric intervention-retention term or a
   high-default gate prior.
```

## Falsified Claims

M784 falsifies:

```text
1. M783 produced a residual calibration candidate.

2. Normal retention alone is enough to advance toward PPO.

3. A low-margin normal suppression loss plus weak intervention floor is
   sufficient to make the gate history/context selective.
```

M784 does not prove:

```text
1. Scalar gates are fundamentally impossible.

2. Vector residual calibration is necessary.

3. PPO is safe.

4. Any checkpoint is promotable.
```

## Failure Taxonomy

Primary failure:

```text
objective_overfit
```

Reason:

```text
The objective found a low-loss global half-gate solution that fixed normal
retention but did not meet the closed-loop intervention gap target.
```

Residual risks:

```text
scenario_sampling_failure
behavior_regression
```

The M773 corpus remains current-model/proxy and hard-negative sparse. Stronger
calibration variants can still reintroduce normal behavior regression.

Not failures:

```text
not contract_violation
not metric_artifact
not private_holdout_contamination
not training_instability
not promotion_gate_failure
not proof_washout
```

## Decision

Decision:

```text
promote_to_asymmetric_residual_gate_design
```

The next branch should keep the same no-PPO safety discipline but change the
calibration objective:

```text
1. gate should be high by default, not initialized/regularized toward 0.5;
2. low-margin normal rows should receive suppression pressure;
3. intervention rows should receive a stronger gate-retention / gap-retention
   target;
4. active-boundary source should remain a required diagnostic;
5. base actor and M761 residual head should remain frozen for the next probe.
```

Next blocker:

```text
m785-v4-asymmetric-residual-gate-design
```

PPO, checkpoint promotion, and base actor mutation remain blocked.
