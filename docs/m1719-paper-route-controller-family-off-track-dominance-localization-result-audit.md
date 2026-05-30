# M1719 Paper-Route Controller-Family Off-Track Dominance Localization Result Audit

- status: completed
- decision: `localized_enough_route_to_repair_panel_design`
- audited artifact: `runs/m1718_off_track_dominance_localization/summary.json`
- audited targets: `runs/m1718_off_track_dominance_localization/repair_target_slices.csv`

## Audit Result

M1718 is a clean no-rollout localization pass and is localized enough to design
a repaired task-quality panel.

Execution and guardrails:

- result class: `off_track_dominance_localization_pass`
- episode rows audited: `864`
- all selected metrics finite: `true`
- guardrail violation count: `0`
- repair target slices: `48`
- variant-source target slices: `34`
- source-task-family target slices: `10`
- variant-task-family target slices: `4`

This audit did not execute rollout, train, replay, run PPO, promote, use private
holdout, change actor inputs, tune profiles, rank controller families, or claim
paper-level evidence or level3 self-identification.

## Localized vs Diffuse Decision

Decision:

```text
localized_enough_for_repair_design
```

The result is not a single-slice problem. There are `48` repair target slices,
and targets appear in both T4 and T5. However, it is also not unstructured
diffuse noise:

- variant-task targets are only `4/8` possible variant-task slices;
- `T4` is overrepresented in variant-task and source-task targets;
- the original baseline remains bad for both T4 and T5;
- `best_off_track_variant::T4` is still above the off-track target threshold;
- several source-task targets have high off-track rate with low collision rate,
  which is exactly the intended repair surface.

The localization is therefore actionable enough for a repair panel, but the
repair panel must remain multi-source and must not collapse to one target row.

## Repair-Relevant Findings

Variant-task targets:

```text
original_axis_baseline::T4      off-track 0.9537 collision 0.0093
original_axis_baseline::T5      off-track 0.9074 collision 0.0648
mid_calibration_variant::T4     off-track 0.8981 collision 0.0370
best_off_track_variant::T4      off-track 0.8241 collision 0.0463
```

Top source-task targets:

```text
t4_staged_warmup_capability|capability_step_up::T4      off-track 0.9167 collision 0.0208
actuator_delay_step|capability_step_up::T4               off-track 0.8958 collision 0.0208
t4_capability_step_temporal|capability_step_down::T4     off-track 0.8750 collision 0.0417
actuator_delay_step|t4_capability_step_temporal::T4      off-track 0.8646 collision 0.0417
t4_actuator_delay_response|actuator_delay_step::T4       off-track 0.8542 collision 0.0625
```

Top individual target:

```text
mid_calibration_variant::capability_step_down|t5_near_boundary_warmup
off-track 1.0000
collision 0.0000
```

## Route Decision

Route to M1720 repair panel design.

M1720 should design a fixed-budget no-rollout repair panel before any execution.
The design should:

- preserve original-axis baseline rows;
- preserve the two conditional-positive calibrated controls from M1716;
- add the missing composite variant `track_width=2.0`, `finish=relaxed`,
  `max_steps=1.5` if available in the M1702 calibration matrix;
- select repair-source rows from M1718 target slices without using profile
  performance as a ranking signal;
- keep T4 emphasis while retaining T5 coverage;
- keep all twelve controller-family profiles as controls;
- pre-register collision/off-track thresholds before any rollout.

## Supported Claims

- M1718 localization artifacts are complete and guardrail-clean.
- Remaining off-track dominance is structured enough for repair-panel design.
- Profile rows remain controls, not ranking evidence.

## Unsupported Claims

- controller-family ranking
- task repair success
- recurrent advantage
- finite-window history necessity
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Decision

M1719 passes as a process audit. Route to M1720 off-track repair panel design.
