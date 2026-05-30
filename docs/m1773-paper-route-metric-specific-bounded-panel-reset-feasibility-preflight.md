# M1773 Paper-Route Metric-Specific Bounded Panel Reset Feasibility Preflight

- status: completed
- result class: `metric_specific_bounded_panel_reset_feasibility_preflight_pass`
- summary: `runs/m1773_metric_specific_bounded_panel_reset_feasibility_preflight/summary.json`
- parent audit: `docs/m1772-paper-route-metric-specific-bounded-panel-materialization-result-audit.md`
- reset-only: true
- policy rollout: false
- training/replay/PPO: false

## Summary

M1773 runs a reset-only feasibility preflight over the M1771 bounded
metric-specific panel. It builds each profile-adjusted environment config,
calls `env.reset(seed=...)`, records the sampled labels and reset metadata, and
does not execute any policy action.

The preflight passes:

```text
attempted_cell_count: 288 / 288
matrix_cell_count: 288 / 288
reset_success_count: 288 / 288
sampling_failure_count: 0
profile_count: 12 / 12
role_panel_count: 4 / 4
metadata_join_incomplete_count: 0
guardrail_violation_count: 0
```

## Role Coverage

The reset rows preserve the bounded role-panel balance:

```text
stable_avoidance_aes: 72 reset-success cells
drift_required_recovery: 72 reset-success cells
hidden_dynamics_robustness: 72 reset-success cells
unavoidable_mitigation: 72 reset-success cells
```

Sampled labels after reset:

```text
aeb_feasible: 36
aes_feasible: 47
drift_required: 105
unavoidable: 100
```

Role-level sampled-label distribution:

```text
stable_avoidance_aes:
  aeb_feasible: 36
  aes_feasible: 36

drift_required_recovery:
  drift_required: 72

hidden_dynamics_robustness:
  aes_feasible: 11
  drift_required: 33
  unavoidable: 28

unavoidable_mitigation:
  unavoidable: 72
```

The hidden-dynamics robustness panel intentionally remains mixed-label because
that role stresses hidden dynamics rather than one obstacle feasibility label.

## Artifacts

```text
runs/m1773_metric_specific_bounded_panel_reset_feasibility_preflight/summary.json
runs/m1773_metric_specific_bounded_panel_reset_feasibility_preflight/reset_stress_rows.csv
runs/m1773_metric_specific_bounded_panel_reset_feasibility_preflight/sampling_failure_rows.csv
runs/m1773_metric_specific_bounded_panel_reset_feasibility_preflight/label_distribution_by_spec.csv
runs/m1773_metric_specific_bounded_panel_reset_feasibility_preflight/label_distribution_by_role.csv
runs/m1773_metric_specific_bounded_panel_reset_feasibility_preflight/label_distribution_by_family.csv
```

`sampling_failure_rows.csv` contains only a header row because there were no
sampling failures.

## Guardrails

- environment reset started: `true`
- policy action executed: `false`
- measured rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- all `288` bounded-panel cells are reset/sampling feasible under their profile
  configs;
- reset rows preserve role, profile, source, metric, and sampled-label metadata;
- no sampling repair is needed before measured-execution design.

Unsupported:

- policy rollout success;
- controller-family ranking;
- profile promotion;
- paper-level benchmark evidence;
- private-holdout evidence;
- level3 self-identification.

## Decision

Route to M1774 reset-result audit before any measured execution design.

M1774 should audit whether the reset-only result is coherent enough to admit a
bounded-panel measured execution design, or whether label/role distribution,
metadata, or guardrail issues require repair first.
