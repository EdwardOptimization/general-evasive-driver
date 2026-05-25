# M793 V4 Residual Component Sensitivity Audit

## Purpose

M793 audits M792 before any new residual objective, replay run, PPO, or
checkpoint promotion.

The question is:

```text
Does M792 provide enough clean component evidence to choose the next residual
calibration branch?
```

This milestone is audit-only:

```text
no replay rerun
no optimizer run
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Cleanliness Check

M792 is a clean diagnostic result:

```text
positive_rows: 2652
reconstructed_rows: 2640
sample_reconstruction_success_rate: 0.995475
metadata_missing_rows: 0
rejected_rows: 12

actor_backbone_changed: false
base_residual_head_changed: false
optimizer_started: false
training_started: false
ppo_used: false
promoted: false
```

The `12` rejected rows are the known unsupported `command_shift_obs` rows from
the current corpus path, not new metadata drift. The actor contract is
unchanged:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

## Evidence Summary

M792 result class:

```text
v4_residual_component_sensitivity_attribution_found
```

The result is attribution-only:

```text
actionable_mask_count: 0
```

No fixed mask simultaneously beats the M786 alpha `0.15` gap reference and
retains the active-source normal margin threshold.

Component roles:

| component | useful | harmful | interpretation |
| --- | --- | --- | --- |
| steer | true | true | main gap source and active-source collision source |
| throttle | false | false | no meaningful role in this diagnostic |
| brake | true | false | weaker useful-only signal |

## Active Source

The binding active source remains:

```text
seed: 77025
source_index: 12
step: 24
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
```

At alpha `0.2`:

```text
all:
  gap mean: 0.046317
  active margin: -0.000062
  collision rate: 0.004545

steer_only:
  gap mean: 0.044286
  active margin: -0.000049
  collision rate: 0.004545

throttle_brake / no_steer:
  gap mean: 0.042545
  active margin: +0.000112
  collision rate: 0.000000
```

This is the decisive pattern:

```text
steer residual carries much of the intervention action separation, but the
same steer residual pushes the active normal source through the collision
boundary.
```

## Interpretation

M792 changes the blocker from:

```text
vector gate did not learn component selectivity
```

to:

```text
component selectivity is needed, and the critical component is steering.
```

The next objective should not be another generic vector gate. M789 already
showed that simply giving the gate three outputs collapsed to scalar-like
behavior. M792 shows why the objective must name the control role:

```text
retain or amplify steering residual when it creates intervention separation;
suppress steering residual on low-normal-margin branches that match the active
boundary failure;
do not spend objective pressure on throttle unless fresh evidence changes its
role.
```

Brake can be retained as a secondary useful component, but it is not the active
normal collision cause in this diagnostic.

## Supported Claims

M793 supports:

```text
1. M792 is a clean no-training diagnostic, not a tooling artifact.

2. Fixed component masks are not sufficient for an actionable Pareto candidate.

3. Steering residual is both the main useful component and the active-source
   harmful component.

4. The next residual-calibration design should be steer-attributed and
   normal-boundary-aware, not a generic scalar or generic vector gate.
```

## Falsified Claims

M793 falsifies:

```text
1. A fixed no-steer mask is enough; it is safe but loses too much intervention
   gap.

2. A fixed steer-only mask is enough; it preserves gap better but remains
   unsafe on the active source.

3. Throttle residual is a useful target for the next objective on the current
   M773/M761 evidence.

4. Another vector gate without explicit steer-boundary terms is the right next
   lever.
```

## Overfit Risk

M792 uses the public M773 broader source-holdout corpus and a known public
active source. It is appropriate for mechanism debugging, but it is not broad
generalization evidence.

M794 must therefore remain design-only and must preserve these constraints:

```text
no PPO
no checkpoint promotion
no broad generalization claim
no weakened M786/M780 thresholds
no tuning from private holdout
```

If the next implementation trains a steer-specific calibrator, it should still
be treated as diagnostic until it passes an audit and, later, fresh-source
validation.

## Decision

M793 classifies M792 as:

```text
clean attribution-only result
```

The next blocker is:

```text
m794-v4-steer-attributed-residual-calibration-design
```

M794 should design a no-PPO steer-attributed residual calibration branch. The
design should test whether a deployable-feature gate can suppress harmful
steering residual on low-normal-margin branches while preserving steering and
brake contribution where intervention separation is needed.

Promotion and PPO remain blocked.
