# M1205 Paper-Route Finite-Window GRU Evidence Synthesis

## Summary

M1205 synthesizes the M1195-M1204 finite-window vs GRU evidence branch.

Decision:

```text
continue_to_corrected_profile_pilot_design
```

The branch should continue, but only through the corrected-control route. Do not
run another M1199-style pilot without current-tiled L2 controls and corrected
L3 reset semantics.

## Evidence Summary

M1195 made the controller-profile masks real in the train/eval vector paths.
That closed the gap where `L0_current_masked` could be masked in single-env
runtime but leak previous-command fields during vectorized training.

M1196 and M1197 proved train-loop plumbing for all generated profiles:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L3_online_gru
L3_reset_control
```

M1198 pre-registered the first fair public pilot and blocked smoke metrics as
comparison evidence.

M1199 ran the public pilot:

```text
24/24 seed runs complete
all eval metrics finite
L2 finite-window family strongest in public pilot trend
no promotion / no private holdout / no self-ID claim
```

M1200 audited the result and blocked direct scaling because of two red flags:

```text
L2 window-equivalence
L3 reset-control parity
```

M1201 separated those issues:

```text
configs_differ_as_intended: true
l2_observation_stacks_nonidentical: true
l2_older_tiled_action_l2_mean_overall: 0.001374
l2_older_zeroed_action_l2_mean_overall: 0.060810
reset_control_external_eval_semantics_mismatch: true
```

This means L2's public pilot trend is real as a trend, but not yet evidence of
finite-window history use. It may be a temporal-GRU/capacity/current-frame
substitution effect. It also means M1199's `L3_reset_control` aggregate was a
diagnostic metric artifact.

M1202 designed the repairs:

```text
reset_hidden_policy-aware public eval
current-tiled L2 capacity controls
```

M1203 implemented the repairs:

```text
ObservationMaskSpec.history_transform = current_tiled
ObservationMaskSpec.reset_hidden_policy metadata
ActorPolicy every_step_control reset semantics
```

M1204 smoke-tested them:

```text
all_smoke_checks_passed: true
single_env_reset_tiled: true
single_env_step_tiled: true
vector_env_reset_tiled: true
vector_env_step_tiled: true
reset_policy_honored: true
```

## Supported Claims

Supported:

```text
The L0/L1/L2/L3 profile infrastructure is now train-loop capable.
The first public pilot ran with fixed budgets and no private holdout.
The short public pilot showed an L2-family trend.
The L2 trend is not clean history-necessity evidence.
The original L3 reset-control diagnostic was flawed.
Corrected reset and current-tiled controls are implemented and smoke-tested.
```

Operationally, the branch is ready to design a corrected public pilot.

## Falsified Or Blocked Claims

Blocked or falsified for now:

```text
GRU > finite-window
finite-window history necessity
L2 promotion
L3 recurrent-hidden benefit
M1199 reset-control parity as a valid diagnostic
paper-level architecture ranking
self-identification
private-holdout generalization
```

The most important blocked claim is:

```text
M1199 L2 advantage proves use of older command-response history.
```

M1201 specifically weakens that interpretation because current-tiled older
history barely changed L2 actions.

## Failure Taxonomy Summary

Primary taxonomy:

```text
metric_artifact
```

Reason:

```text
M1199 external eval did not enforce L3_reset_control every-step hidden reset.
```

Secondary process risk:

```text
current_frame_substitution_risk
```

This is tracked in the self-identification discipline rather than as a core
failure taxonomy label. It blocks history-necessity claims until current-tiled
controls are included in the public pilot.

## Public-Gate Overfit Risk

Risk is moderate.

Reasons:

```text
M1199 used fixed public seeds and short budgets.
The same public artifacts drove M1200-M1204.
L2 controls were designed after seeing M1199, so later comparisons must clearly mark them as corrected-public evidence.
```

Mitigations already in place:

```text
private holdout remains unused;
no checkpoint was promoted;
no profile-specific hyperparameters were tuned;
corrected controls are evaluated first on public evidence only;
paper-level claims remain blocked.
```

The next corrected pilot should still be public diagnostic evidence. Private
holdout should remain blocked until the corrected public protocol is stable.

## Next Branch Decision

Continue the branch.

Next milestone:

```text
experiments/manifests/m1206-paper-route-corrected-profile-pilot-design.json
```

M1206 should design the corrected public pilot with:

```text
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L3_online_gru
L3_reset_control_corrected
```

The design must fix:

```text
same training seeds and budgets for every profile;
same public eval seeds for every checkpoint;
reset_hidden_policy honored in evaluation;
current-tiled controls trained and evaluated through the same runtime transform;
no private holdout;
no promotion;
no self-ID or paper-level claim.
```

If M1206 cannot keep those constraints, the branch should pivot to profile
repair instead of running another pilot.
