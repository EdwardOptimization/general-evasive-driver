# M1758 Single Sampling Failure Reset-Only Feasibility Probe

- status: completed
- result class: `seed_fragile_but_feasible`
- output dir: `runs/m1758_single_sampling_failure_reset_only_probe`
- policy rollout: false
- training/replay/PPO: false

## Summary

M1758 probes the single M1756/M1757 reset-time sampling failure without running
policy rollout or changing scenario/profile specs. The exact failed seed still
fails, but the same workload is feasible for most neighboring deterministic
seeds.

This classifies the blocker as seed-fragile sampling, not a spec-filter
infeasibility. The next substantive route should therefore be a pre-registered
single-cell seed repair/completion design rather than scenario-spec repair.
Because the branch synthesis cadence has fired, M1759 must synthesize the
M1749-M1758 branch before that seed-repair design is admitted.

## Probe Setup

```text
workload_id: m1728-s4-02::L2_window_13_current_tiled
scenario_spec_id: m1728-s4-02
profile_name: L2_window_13_current_tiled
scenario_family: unavoidable_mitigation
evaluation_role: mitigation_diagnostic
primary_metric_family: collision_mitigation
hidden_dynamics_bucket: low_mu
exact_seed: 175761
neighbor_radius: 50
probe_seed_count: 101
```

The probe reconstructed the M1756 cell from:

```text
metadata specs: runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_specs.json
executable specs: runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.json
workload matrix: runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_matrix.csv
```

## Result

```text
result_class: seed_fragile_but_feasible
exact_reset_success: false
success_count: 95
failure_count: 6
neighbor_success_count: 95
neighbor_failure_count: 5
sampled_label_counts: unavoidable=95
```

Failed seeds:

```text
175761 exact offset 0
175755 neighbor offset -6
175777 neighbor offset 16
175789 neighbor offset 28
175793 neighbor offset 32
175796 neighbor offset 35
```

The nearest successful deterministic seeds are `175760` and `175762`, both at
absolute offset `1`, and both sample the intended `unavoidable` label.

## Interpretation Boundary

Supported:

- the exact M1756 seed is reproducibly infeasible for this reset sampler;
- the same scenario/profile/spec combination is feasible for nearby seeds;
- scenario-spec repair is not justified before a seed-repair completion design.

Unsupported:

- policy rollout result;
- controller-family ranking;
- profile comparison;
- paper-level benchmark evidence;
- private-holdout evidence;
- level3 self-identification evidence.

## Guardrails

- policy rollout started: `false`
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

Route to M1759 revised scenario-taxonomy branch synthesis, with a provisional
next-branch recommendation to design a single-cell seed-repair completion route.
Use the nearest successful seed as a pre-registered replacement candidate and
preserve the seed override as explicit provenance. Do not silently drop the
missing row, change scenario specs, or interpret M1756/M1758 partial evidence as
a ranking result.
