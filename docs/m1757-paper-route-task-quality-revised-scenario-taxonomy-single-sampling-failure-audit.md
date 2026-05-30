# M1757 Paper-Route Task-Quality Revised Scenario Taxonomy Single Sampling Failure Audit

- status: completed
- decision: `single_sampling_failure_audit_admit_reset_only_probe`
- audited rerun: `docs/m1756-paper-route-task-quality-revised-scenario-taxonomy-rerun-after-wrapper-repair.md`
- no rollout: true
- training/replay/PPO: false

## Summary

M1757 audits the single remaining M1756 failure. The M1755 wrapper repair is
confirmed: AttributeError failures are zero. The only blocker is one reset-time
sampling failure in a mitigation-diagnostic row.

The next step should be a reset-only feasibility probe over that exact row and
nearby deterministic seeds. Do not change specs or execution seed before the
probe explains whether the row is infeasible, seed-fragile, or simply needs a
bounded sampling repair.

## Localized Failure

```text
workload_id: m1728-s4-02::L2_window_13_current_tiled
workload_index: 461
eval_seed: 175761
scenario_spec_id: m1728-s4-02
profile_name: L2_window_13_current_tiled
scenario_family: unavoidable_mitigation
evaluation_role: mitigation_diagnostic
primary_metric_family: collision_mitigation
obstacle_timing_bucket: close
obstacle_lateral_bucket: mild_offset
road_boundary_bucket: moderate
hidden_dynamics_bucket: low_mu
sampling_repair_source: m1728_original
sampling_repair_variant_id: no_sampling_repair_needed
error_type: RuntimeError
error_message: failed to sample an obstacle scenario matching the configured filters
```

M1756 aggregate status:

```text
episode_count: 863
target_episode_count: 864
failure_count: 1
attribute_error_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

## Interpretation Boundary

M1756 is still incomplete. Its completed rows are not controller-family ranking
evidence and are not paper-level benchmark evidence. The single missing row
touches a mitigation-diagnostic metric family, so it should not be silently
dropped.

## Probe Route

Admit M1758 reset-only feasibility probe:

- use the exact M1756 failed row;
- reconstruct the same executable env config and profile config;
- attempt `env.reset(seed=175761)` without policy rollout;
- probe a bounded neighboring seed window around `175761`;
- record sampled labels or failure messages;
- do not change scenario specs, profile configs, actor inputs, rewards,
  dynamics, termination behavior, or execution seeds in the probe milestone.

The probe should classify the row as:

```text
exact_seed_infeasible
seed_fragile_but_feasible
spec_filter_infeasible
probe_inconclusive
```

## Guardrails

- full rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Decision

Route to M1758 single-row reset-only feasibility probe before any spec repair,
seed redesign, or revised execution rerun.
