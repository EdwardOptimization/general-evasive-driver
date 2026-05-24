# M699 Fresh Trajectory-Boundary Sampler Audit

## Purpose

M699 audits the M698 `fresh_surface_empty` result before allowing any further
source-miner modification.

This milestone is process-only:

```text
no rerun
no threshold relaxation
no objective design
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M698 implementation was clean:

```text
actor_parameters_changed: false
training_started:         false
ppo_used:                 false
promoted:                 false
```

Fresh sampling covered:

```text
episodes_attempted: 512
episodes_completed: 512
snapshots_collected: 4056
prepass_rows: 4056
```

Episode outcomes:

```text
obstacle_completed: 337
collision:          175
```

Prepass distribution:

```text
failed:              1360
too_safe:            2168
wide_but_sensitive:   384
near_boundary:         112
terminal_cliff:         32
```

The sampler did find 528 non-failed and non-too-safe windows, but none were
sensitive under the registered perturbation grid:

```text
perturbation_evaluated_rows: 528
accepted_rows:                0
trajectory_boundary_rows:     0
history_action_critical_rows: 0
result_class: fresh_surface_empty
```

Sensitivity summary:

```text
margin_sensitivity_mean: 0.000338
margin_sensitivity_p95:  0.001687
margin_sensitivity_max:  0.005952
threshold:               0.020000

history_margin_gap_p95:  0.000009
history_margin_gap_max:  0.000100
```

## Supported Claims

The evidence supports:

```text
1. The fresh sampler can collect and replay fresh scenario snapshots without
   mutating the actor.

2. The M698 seed/config/window recipe produces a bimodal source distribution:
   many rows are already failed, many pass with large margin, and the moderate
   boundary windows are locally insensitive.

3. The current perturbation grid is not enough to expose terminal-margin
   sensitivity on the collected non-failed windows.

4. Objective design, actor update, PPO, and promotion remain blocked.
```

## Falsified Claims

The evidence falsifies:

```text
1. The registered M698 fresh sampler already produced an objective-ready source.

2. The M692-row-only surface was the only reason source mining failed; fresh
   sampling also fails under the current window and perturbation scale.

3. Small first-action perturbations up to steer +/-0.04 and throttle/brake
   +/-0.06 are sufficient to reveal terminal-margin-sensitive rows in this
   distribution.
```

The evidence does not yet falsify:

```text
trajectory-terminal boundary mining as a branch
```

because M698 did not test a perturbation-scale ladder, closer target obstacle
distances, broader action overrides, or scenario-parameter search specifically
designed to create boundary cases.

## Failure Taxonomy Summary

Primary label:

```text
scenario_sampling_failure
```

Reason:

```text
The sampled scenario/window distribution did not produce accepted
terminal-margin-sensitive rows.
```

Secondary label:

```text
metric_artifact
```

Reason:

```text
Earlier exact residual diagnostics and current fresh sampling both generated
large artifact tables without producing source rows that support closed-loop
trajectory evidence.
```

Not classified as:

```text
training_instability:
  no training occurred

contract_violation:
  actor inputs were unchanged

proof_washout:
  actor parameters were unchanged
```

## Public Gate Overfit Risk

The risk remains real but has changed form.

M698 is no longer overfitting M692 rows. It samples fresh seeds. The new risk is
process-level:

```text
repeatedly changing sampling thresholds until accepted rows appear
```

without proving that those rows are meaningful. To avoid that, the next change
must be registered as a diagnostic ladder:

```text
same base actor
same no-training rule
explicit perturbation scales
explicit window targets
result interpreted as sensitivity-scale evidence, not success
```

## Next Branch Decision

Synthesis decision:

```text
continue
```

Branch remains:

```text
trajectory_terminal_boundary_source_mining
```

Next evidence axis:

```text
G_source_scale: determine whether source_empty is caused by too-small
first-action perturbations / missed windowing, or by a base-policy distribution
that has no local terminal boundary under reasonable perturbations.
```

## Next Design Target

M700 should design a sensitivity-scale diagnostic, not an objective.

It should compare:

```text
target_obstacle_distance: 2.0, 1.0, 0.0, -1.0
max_prepass_margin:      0.50, 1.00
steer delta scale:       0.04, 0.08, 0.12, 0.20
brake/throttle scale:    0.06, 0.12, 0.20
continuation:            40 steps
```

It should report:

```text
accepted rows per scale
margin/risk sensitivity per scale
flip counts per scale
normal-failed and too-safe ratios per window
whether any scale creates useful rows without becoming unrealistic
```

It must not:

```text
train actor
run PPO
promote checkpoint
call large unrealistic action overrides a deployable objective
```

If no sensitivity appears even at larger but still plausible action scales, the
branch should pivot toward:

```text
scenario construction / base capability improvement
```

rather than another source-miner tweak.

## Decision String

```text
fresh_sampler_empty_continue_with_sensitivity_scale_design
```

## Next

```text
m700-boundary-sensitivity-scale-diagnostic-design
```
