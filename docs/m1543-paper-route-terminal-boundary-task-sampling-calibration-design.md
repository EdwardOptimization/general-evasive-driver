# M1543 Paper-Route Terminal-Boundary Task-Sampling Calibration Design

## Summary

M1543 designs the task-sampling calibration route admitted by M1542.

Decision:

```text
terminal_boundary_task_sampling_calibration_design_admit_bounded_implementation
```

M1541 showed that terminal source families can produce accepted pairs and stable
intervention replay, but their fixed-policy decision states did not enter the
intended near-boundary active set. M1543 therefore changes the next step from
another intervention rerun to a bounded calibration pass that targets actual
simulator margins before history interventions are allowed.

This is design only. It does not train, replay interventions, run PPO, promote,
use private holdout, export a training corpus, materialize candidates, alter
actor inputs, or claim level3 self-identification.

## Problem Statement

M1541 failed the source-window gate:

```text
terminal_target_trace_count: 20
terminal_target_near_boundary_count: 0
```

It also failed the evidence gates:

```text
terminal_wrong_history_positive_target_sides: 0
terminal_donor_plus_hidden_positive_target_sides: 0
terminal_max_history_margin_gap: 0.0040251709543639436
terminal_max_control_margin_gap: 0.14847354874699903
terminal_control_to_history_gap_ratio: 36.88627152246277
```

The root cause is not yet a policy limitation. The immediate root cause is that
the target tasks are not calibrated to the terminal-boundary decision surface.
The next experiment must first produce actual fixed-policy near-boundary rows.

## Design Goal

Generate a bounded public calibration table:

```text
terminal source family
  -> retargeted env hook
  -> fixed-policy trace
  -> decision/post-decision margin measurement
  -> calibrated row if actual margin enters target window
```

This table is a development artifact only. It is not a training corpus and does
not materialize RL candidates.

## Target Families

Use the same terminal target families as M1541:

```text
t5_near_boundary_warmup
t5_high_speed_close_obstacle
t5_boundary_axis_retarget
late_reveal_boundary
curved_boundary_obstacle
```

Support/proxy families may be recorded for diagnostics, but M1544 should count
calibration success by terminal target family. A terminal-boundary claim
requires the target side to be one of the five terminal families.

## Calibration Variables

The implementation should start from `source_row_to_hook_spec(row)`, then create
retargeted P0 env configs by changing simulator task parameters only:

```text
obstacle.distance_range scale: 0.55, 0.62, 0.70, 0.80, 0.90
obstacle.half_width_range shift: 0.20, 0.40, 0.60, 0.80
speed_range shift: 0.0, 1.5, 3.0
reveal_step delta: -4, 0, +4, +8
decision_step follows reveal_step + existing offset unless explicitly bounded
optional require_aeb_infeasible: false, true
optional low authority band: mu/brake/tire low-range only as simulator config
```

Keep the grid bounded. M1544 should cap candidate specs before rollout:

```text
source_seed: 1843
source_seed_count: 2
max_base_rows: 20
max_calibration_specs: 160
max_rollout_steps: 128
device: cpu
checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

The design allows hidden-capability and simulator-randomization metadata for
logging and filtering only. These values must not enter actor input.

## Margin Windows

Separate decision-window and post-decision-window calibration:

```text
decision_margin_window: [-0.03, 0.12]
preferred_decision_margin_window: [-0.01, 0.06]
post_decision_margin_window: [-0.05, 0.10]
terminal_margin_window: [-0.05, 0.12]
```

Acceptance can use either:

```text
decision window hit
or
post-decision window hit
```

but the artifact must record which window fired. A later intervention rerun
should prioritize decision-window hits first, then post-decision hits.

## Required Artifacts

M1544 should write:

```text
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/source_rows.csv
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/calibration_specs.csv
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/trace_rows.csv
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/snapshot_rows.csv
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/accepted_calibrated_rows.csv
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/family_summary.csv
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/guardrail_summary.csv
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/summary.json
```

No training corpus file should be written.

## Pass / Fail Gates

Calibration source gates:

```text
terminal_base_source_rows >= 10
calibration_spec_count >= 40
terminal_target_trace_count >= 20
terminal_family_count >= 4
guardrail_violation_count == 0
```

Near-boundary gates:

```text
accepted_calibrated_row_count >= 8
accepted_terminal_family_count >= 3
decision_window_hit_count >= 4
post_decision_window_hit_count >= 4
max_single_terminal_family_share <= 0.50
```

Quality gates:

```text
finite_margin_row_count == trace_or_snapshot row count used for calibration
actor_input_contract_changed == false
candidate_materialized == false
training_corpus_exported == false
training_started == false
ppo_used == false
private_holdout_used == false
level3_self_id_claim_made == false
```

If accepted calibrated rows are below threshold, classify as:

```text
scenario_sampling_failure
```

If rows are accepted but dominated by one terminal family, classify as:

```text
objective_overfit
```

If calibration requires actor-input or reward/label shortcuts, classify as:

```text
contract_violation
```

## Next Route After Calibration

If M1544 passes, it should not immediately train. The next admitted step should
be a design for calibrated terminal-boundary history interventions:

```text
calibrated accepted rows
  -> matched scene/current-state pair building
  -> wrong-history / donor-plus-hidden / donor-stream / delayed / reset / zero controls
  -> terminal history-positive gate
```

If M1544 fails because no calibrated rows can be found, the branch should route
to synthesis instead of adding another narrow source tweak.

## Guardrails

```text
candidate_materialized: false
training_started: false
evaluation_started: false
replay_started: false
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
m1544-paper-route-terminal-boundary-task-sampling-calibration-implementation
```
