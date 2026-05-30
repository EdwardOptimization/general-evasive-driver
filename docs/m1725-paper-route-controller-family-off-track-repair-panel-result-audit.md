# M1725 Paper-Route Controller-Family Off-Track Repair Panel Result Audit

- status: completed
- decision: `conditional_repair_retained_route_to_branch_synthesis`
- audited artifact: `runs/m1724_off_track_repair_panel_execution/summary.json`
- audited variant aggregate: `runs/m1724_off_track_repair_panel_execution/repair_variant_aggregate.csv`

## Audit Result

M1724 is a clean measured off-track repair panel execution with a conditional
repair signal, but not a full or composite-positive repair result.

Execution plumbing:

- result class: `controller_family_off_track_repair_panel_execution_pass`
- episode count: `864` / `864`
- failure count: `0`
- all selected metrics finite: `true`
- guardrail violation count: `0`
- repair variant aggregate rows: `4`
- outcome aggregate rows: `4`
- termination reason aggregate rows: `4`

This audit did not execute rollout, train, replay, run PPO, promote, use private
holdout, change actor inputs, tune profiles, rank controller families, or claim
paper-level evidence or level3 self-identification.

## Pre-Registered Variant Comparison

Baseline:

```text
variant: original_axis_baseline
off_track_noncollision_noncompletion_rate: 0.9352
collision_failure_rate: 0.0324
```

Non-baseline repair variants:

| variant | off-track | collision | off-track improvement | collision delta | M1723 rule |
| --- | ---: | ---: | ---: | ---: | --- |
| `best_off_track_variant` | `0.7361` | `0.1019` | `0.1991` | `0.0694` | tradeoff risk |
| `collision_control_wide_relaxed` | `0.7824` | `0.0648` | `0.1528` | `0.0324` | conditional repair retained |
| `wide_relaxed_extended` | `0.7315` | `0.0833` | `0.2037` | `0.0509` | composite miss |

Composite check for `wide_relaxed_extended`:

```text
prior_control_best_offtrack: 0.7361
wide_relaxed_extended_offtrack: 0.7315
composite_delta_vs_prior_best: -0.0046
required composite_delta_vs_prior_best: <= -0.0300
```

## Result Classification

```text
result_class: conditional_repair_retained
full_repair_positive: false
composite_repair_positive: false
conditional_repair_retained: true
tradeoff_only: false
repair_failed: false
runner_failure: false
```

Why not `full_repair_positive`:

```text
wide_relaxed_extended off-track is 0.7315, above the 0.70 threshold;
wide_relaxed_extended collision delta is 0.0509, just above the 0.05 guard.
```

Why not `composite_repair_positive`:

```text
wide_relaxed_extended improves off-track versus prior-control best by only
0.0046, below the required 0.0300 composite margin, and its collision delta is
0.0509.
```

Why not `tradeoff_only`:

```text
collision_control_wide_relaxed improves off-track by 0.1528 with collision
delta 0.0324, inside the 0.05 guard.
```

Why not `repair_failed`:

```text
at least one non-baseline variant improves off-track by >= 0.10 inside the
collision guard, and not all non-baseline variants remain above the 0.80
off-track failure boundary.
```

## Interpretation Boundary

Supported:

- The repair panel execution path is clean.
- The repair axes can reduce off-track dominance under at least one
  collision-guarded variant.
- The new composite `wide_relaxed_extended` variant does not provide the
  pre-registered composite-positive improvement.
- Branch synthesis is required before another repair panel, broader scale-up, or
  controller-family comparison.

Unsupported:

- controller-family ranking
- recurrent advantage
- finite-window history necessity
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Decision

M1725 passes as a process audit. Route to M1726 branch synthesis before further
task-quality repair, broader scenario design, controller-family comparison, or
paper-route claims.
