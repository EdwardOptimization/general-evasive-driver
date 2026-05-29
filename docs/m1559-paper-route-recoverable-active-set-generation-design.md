# M1559 Paper-Route Recoverable Active-Set Generation Design

## Summary

M1559 designs the first milestone in the new branch:

```text
paper_route_recoverable_active_set_generation
```

Decision:

```text
recoverable_active_set_generation_design_admit_bounded_generator
```

The core change is:

```text
generate recoverable active-set anchors first;
only after that consider history interventions.
```

M1558 closed the calibrated pair-expansion branch because pair coverage was no
longer the main blocker. The current blocker is source generation: the project
needs source-diverse anchors where the fixed actor is close to a terminal
boundary and bounded local control can still change the outcome.

No implementation smoke, history intervention, candidate materialization,
training corpus export, training, PPO, promotion, private holdout, actor-input
change, or level3 self-identification claim is admitted by M1559.

## Why Recoverable Active Set

M1556/M1557 showed two bad regimes:

```text
1. already-colliding near-boundary anchors:
   abs(normal_margin) <= 0.1 but terminal reason is collision and local action
   holds do not recover the outcome;

2. high-margin safe anchors:
   normal_margin is large positive and some overrides affect completion timing,
   but this is not terminal-boundary evidence.
```

The next generator must explicitly search for the middle regime:

```text
recoverable-boundary anchors:
  normal trajectory is close to success/collision boundary;
  bounded local action changes can alter terminal margin or outcome;
  the effect is source-diverse and appears before the terminal outcome is already fixed.
```

## Source Generation Scope

M1560 should build a no-training source generator over public simulator knobs:

```text
obstacle distance range;
obstacle half-width range;
obstacle lateral offset / side;
perception reveal step;
decision step proxy;
initial speed range;
track curvature / obstacle curve family;
friction and actuator-lag source families already supported by current hooks.
```

Do not add wheel-specific failures such as puncture, individual tire loss, or
half-shaft breakage as true labels in this branch. The current single-track P0
simulator cannot faithfully represent those physical faults. They can remain
future simulator-fidelity tasks. For this branch, use existing source-family
capability proxies only.

## Anchor Windows

M1560 should test anchors before the outcome is fixed:

```text
reveal
reveal_plus_4
decision_minus_24
decision_minus_16
decision_minus_8
decision
```

If windows collapse onto the same simulator step, de-duplicate by:

```text
calibration_id@anchor_step
```

## Local Controllability Diagnostics

M1556 used one-step overrides. That was too weak for many near-collision rows
and too easy to misread as completion-timing change on high-margin rows.

M1560 should add bounded multi-step local holds:

```text
hold_steps: 1, 4, 8, 12
```

Local override families:

```text
steer_left
steer_right
brake_more
brake_less
throttle_release
steer_left_brake_more
steer_right_brake_more
steer_left_brake_less
steer_right_brake_less
```

After the hold, the same fixed actor resumes. This remains a diagnostic, not a
rule-controller policy or training target.

## Triage Labels

M1560 should classify each successful anchor replay:

```text
already_colliding:
  normal_collision == true
  and no local hold flips collision/success
  and max_abs_margin_gap < 0.02

high_margin_safe:
  normal_success == true
  and normal_terminal_margin > 0.50
  and no collision flip

recoverable_boundary:
  abs(normal_terminal_margin) <= 0.50
  and at least one local hold has:
      terminal_margin_gap >= 0.02
      or success_flip == true
      or collision_flip == true

strong_recoverable_boundary:
  abs(normal_terminal_margin) <= 0.25
  and at least one local hold has:
      terminal_margin_gap >= 0.05
      or collision_flip == true
```

Only recoverable-boundary anchors can be admitted to later history-intervention
design. High-margin safe and already-colliding rows should remain diagnostics.

## M1560 Public Gates

M1560 should pass only if all guardrails are clean and these minimums hold:

```text
source_spec_count >= 160
anchor_candidate_count >= 256
replay_ok_anchor_count >= 128
recoverable_boundary_anchor_count >= 24
strong_recoverable_boundary_anchor_count >= 8
predecision_recoverable_anchor_count >= 12
active_source_family_count >= 4
active_window_count >= 3
max_single_active_family_share <= 0.35
max_single_active_window_share <= 0.45
collision_flip_count >= 4
or success_flip_count >= 8
```

Evidence-quality targets:

```text
recoverable_boundary_anchor_count >= 48
strong_recoverable_boundary_anchor_count >= 16
active_source_family_count >= 5
active_window_count >= 4
max_single_active_family_share <= 0.30
near_boundary_collision_only_share <= 0.40
high_margin_active_share <= 0.25
```

If M1560 fails these gates, route to audit before any further generator.

## Required Artifacts

M1560 should write:

```text
runs/m1560_recoverable_active_set_generator_smoke/source_spec_rows.csv
runs/m1560_recoverable_active_set_generator_smoke/anchor_candidate_rows.csv
runs/m1560_recoverable_active_set_generator_smoke/local_hold_rows.csv
runs/m1560_recoverable_active_set_generator_smoke/recoverable_active_anchor_rows.csv
runs/m1560_recoverable_active_set_generator_smoke/triage_summary.csv
runs/m1560_recoverable_active_set_generator_smoke/source_family_summary.csv
runs/m1560_recoverable_active_set_generator_smoke/window_summary.csv
runs/m1560_recoverable_active_set_generator_smoke/guardrail_summary.csv
runs/m1560_recoverable_active_set_generator_smoke/summary.json
```

Do not write:

```text
history intervention rows;
training corpus;
checkpoint;
promotion artifact.
```

## Follow-Up Logic

If M1560 passes public active-set gates:

```text
M1561 audits source diversity, triage composition, and local-control evidence.
M1562 may design history interventions only over recoverable-boundary anchors.
```

If M1560 fails:

```text
M1561 audits whether the issue is scenario sampling, local hold design, or simulator limitation.
Do not run history interventions.
```

## Guardrails

```text
history_interventions_executed: false
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1560-paper-route-recoverable-active-set-generator-implementation
```
