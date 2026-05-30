# M1765 Single-Cell Seed-Repair Completion Result Audit

- status: completed
- decision: `completion_result_audit_admit_completed_taxonomy_outcome_audit`
- audited output: `runs/m1764_revised_scenario_taxonomy_single_seed_completion`
- no rollout: true
- training/replay/PPO: false

## Summary

M1765 audits the M1764 completed artifact. The completion gates pass:

```text
episode_count: 864
failure_count: 0
profile_count: 12
scenario_spec_count: 72
scenario_family_count: 6
all_selected_metrics_finite: true
metric_completeness_passed: true
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

The artifact has exactly one seed-repair row, and the original failed row is
preserved separately. This is valid completion evidence for the revised public
diagnostic matrix. It is not yet controller-family ranking or paper-level
benchmark evidence.

## Seed-Repair Audit

```text
seed_repair_applied_row_count: 1
workload_id: m1728-s4-02::L2_window_13_current_tiled
original_eval_seed: 175761
replacement_eval_seed: 175760
replacement_seed_offset: -1
seed_repair_rule: nearest_successful_neighbor_tie_lower
seed_repair_source: m1758_single_sampling_failure_reset_only_probe
sampled_obstacle_label: unavoidable
```

The provenance is explicit and auditable:

```text
seed_repair_provenance.csv
original_failure_rows.csv
```

M1764 did not silently drop the failed row, mutate M1756 outputs, or change
scenario/profile specs.

## Outcome Snapshot

Completed matrix outcome counts:

```text
success_obstacle_pass: 73
collision_failure: 280
off_track_noncollision_noncompletion: 511
```

By evaluation role:

```text
benchmark: 41 success, 50 collision, 341 off-track
diagnostic_stress: 28 success, 92 collision, 168 off-track
mitigation_diagnostic: 4 success, 138 collision, 2 off-track
```

This snapshot shows the completed artifact is still outcome-dominated. The next
step should audit outcomes by revised semantics before any ranking or paper
claim.

## Guardrails

- environment rollout started in this audit: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile configs changed: `false`
- scenario specs changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- M1764 is a valid completed public diagnostic artifact;
- seed-repair provenance is complete and explicit;
- the completed matrix should now be eligible for a revised outcome audit.

Unsupported:

- controller-family ranking;
- profile comparison;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification evidence.

## Decision

Route to M1766 completed taxonomy outcome audit. M1766 should interpret the
completed matrix under M1743/M1750 outcome semantics while still blocking direct
controller-family ranking and paper-level claims.
