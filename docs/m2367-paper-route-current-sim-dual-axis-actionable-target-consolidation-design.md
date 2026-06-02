# M2367 Paper-Route Current-Sim Dual-Axis Actionable Target Consolidation Design

- status: completed
- decision: `actionable_target_consolidation_design_admit_artifact_only_materializer`
- manifest: `experiments/manifests/m2367-paper-route-current-sim-dual-axis-actionable-target-consolidation-design.json`
- parent audit: `docs/m2366-paper-route-current-sim-dual-axis-measured-outcome-localization-result-audit.md`
- reset/rollout/measured execution in M2367: `false`
- policy action executed in M2367: `false`
- training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID claims: `false`

## Design Goal

M2367 designs an artifact-only consolidation pass over the M2365 localization
panel:

```text
source summary:
  runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/summary.json

source slices:
  runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/slice_rows.csv

source slice_row_count:
  313
```

M2365 produced overlapping aggregate slices. M2367 therefore does not route
directly to training or scenario repair. It defines deterministic consolidation
rules for a materializer that separates:

```text
ordinary offtrack repair targets
ordinary offtrack targets that require collision guardrails
collision guardrail only rows
R4 mitigation semantics rows
diagnostic-only guardrail rows
```

## Axis Policy

Diagnostic-only axes:

```text
global
pack_id
profile_name
sampling_repair_class
pack_id + role_family
profile_name + role_family
pack_id + profile_name + role_family
```

These rows may become guardrails or diagnostics only. They must not become
actionable repair targets, profile rankings, pack rankings, or winner
selection evidence.

Actionable axes:

```text
role_family
scenario_family_id
sampled_obstacle_label
hidden_dynamics_bucket
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_bucket
role_family + hidden_dynamics_bucket
role_family + obstacle_longitudinal_timing_bucket
role_family + obstacle_lateral_offset_bucket
```

These rows can become bounded target or guardrail rows because they describe
task semantics, scene/timing geometry, and hidden-dynamics stress rather than a
controller/profile identity.

## Consolidation Rules

Use the M2365 route flags without retuning thresholds:

```text
source minimum_slice_episode_count: 30
source offtrack_target_threshold: 0.70
source high_priority_offtrack_threshold: 0.85
source collision_guardrail_threshold: 0.15
```

Classification precedence:

```text
1. If is_r4_mitigation_semantics is true:
     consolidated_route = r4_mitigation_semantics
     ordinary repair target = false

2. Else if slice_axis is diagnostic-only:
     consolidated_route = diagnostic_guardrail
     ordinary repair target = false

3. Else if is_offtrack_target and is_collision_guardrail:
     consolidated_route = offtrack_repair_target_with_collision_guardrail

4. Else if is_offtrack_target:
     consolidated_route = offtrack_repair_target

5. Else if is_collision_guardrail:
     consolidated_route = collision_guardrail

6. Else:
     consolidated_route = diagnostic_only
```

Each consolidated row should preserve:

```text
slice_axis
slice_value
episode_count
success_rate
offtrack_rate
collision_rate
dominant_failure_mode
is_high_priority_offtrack
source_route_class
consolidated_route
actionability_class
repair_target_admissible
collision_guardrail_required
r4_mitigation_semantics
diagnostic_only
ranking_admissible
winner_selected
paper_level_claim_made
finite_window_vs_gru_conclusion_made
level3_self_id_claim_made
```

Actionability classes:

```text
role_semantics
geometry_timing
hidden_dynamics
role_conditioned_geometry_timing
role_conditioned_hidden_dynamics
r4_mitigation_semantics
diagnostic_guardrail
diagnostic_only
```

## Expected Materializer Outputs

M2368 should write:

```text
runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/summary.json
runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/consolidated_rows.csv
runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/offtrack_repair_target_rows.csv
runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/collision_guardrail_rows.csv
runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/r4_mitigation_semantics_rows.csv
runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/diagnostic_guardrail_rows.csv
runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/claim_boundary.csv
```

## Frozen M2368 Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_actionable_target_consolidation \
  --summary runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/summary.json \
  --slice-rows runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/slice_rows.csv \
  --output-dir runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation \
  --target-slice-row-count 313 \
  --minimum-actionable-episode-count 30 \
  --next-blocker m2369-paper-route-current-sim-dual-axis-actionable-target-consolidation-result-audit
```

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_dual_axis_actionable_target_consolidation.py
```

## Pass Gates

M2368 passes only if:

```text
source_slice_row_count == 313
consolidated_row_count > 0
offtrack_repair_target_row_count > 0
collision_guardrail_row_count > 0
r4_mitigation_semantics_row_count > 0
diagnostic_guardrail_row_count > 0
diagnostic_axis_repair_target_count == 0
r4_ordinary_repair_target_count == 0
ranking_admissible_count == 0
winner_selected_count == 0
guardrail_violation_count == 0
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
paper_level_claim_made == false
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
scenario_redesign_executed_claim_made == false
training_repair_success_claim_made == false
```

## Claim Boundary

M2367 may claim only:

```text
artifact-only actionable target consolidation design over M2365 localization
slices.
```

Still blocked:

```text
controller-family ranking
support-policy ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
scenario redesign executed
training repair success
```

## Next

Pre-register:

```text
m2368-paper-route-current-sim-dual-axis-actionable-target-consolidation-implementation
```
