# M2360 Paper-Route Current-Sim Dual-Axis Repaired Pack Reset Validation Result Audit

- status: completed
- decision: `repaired_pack_reset_validation_result_accepted_route_to_measured_execution_design`
- manifest: `experiments/manifests/m2360-paper-route-current-sim-dual-axis-repaired-pack-reset-validation-result-audit.json`
- audited summary: `runs/m2359_paper_route_current_sim_dual_axis_repaired_pack_reset_validation/summary.json`
- reset rerun in M2360: `false`
- rollout/measured execution in M2360: `false`
- policy action executed: `false`
- training/replay/PPO: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`

## Audit Result

M2360 accepts M2359 as a clean repaired-pack reset-validation pass.

Audited gates:

```text
result_class: current_sim_dual_axis_repaired_pack_reset_validation_pass
input_config_pack_count: 5
scenario_specs_per_pack_count: 72
reset_attempt_count: 360
reset_success_count: 360
reset_failure_count: 0
observation_finite_count: 360
observation_dimension_failure_count: 0
obstacle_initialized_count: 360
contract_violation_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
```

Repair metadata gates:

```text
baseline_env_config_fallback_count: 32
repair_action_row_count: 32
repair_action_reset_row_count: 32
repair_action_rows_preserved: true
repair_class_counts:
  timing_related: 27
  hidden_only: 3
  lateral_hidden: 2
metadata_caveat_row_count: 78
metadata_only_patch_count: 37
metadata_caveat_rows_preserved: true
unresolved_patch_count: 0
```

Effective modified selections:

```text
g_primary_pack: 4
h_primary_pack: 12
g_h_primary_pack: 16
gh_minimal_pack: 14
```

## Interpretation

The five M2356 repaired candidate config packs are reset-valid under the current
simulator and the strict P0 human-view no-wheel 72-dim actor contract.

This is task-quality evidence only. It does not execute a closed-loop policy and
therefore does not measure driving performance, controller-family quality,
finite-window vs GRU behavior, or self-identification.

## Claim Boundary

Allowed claim:

```text
the M2356 repaired five-pack scenario family is reset-valid and admissible for
a separately designed measured-execution run.
```

Still blocked:

```text
scenario redesign executed;
controller-family ranking;
support-policy ranking;
winner selection;
paper-level benchmark evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Decision

Decision:

```text
repaired_pack_reset_validation_result_accepted_route_to_measured_execution_design
```

M2361 should design a bounded measured-execution protocol over the reset-valid
repaired pack family. M2361 must remain design-only: no rollout, no policy
action execution, no ranking, and no paper-level interpretation.
