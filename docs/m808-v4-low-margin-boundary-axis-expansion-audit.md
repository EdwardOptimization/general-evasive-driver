# M808 V4 Low-Margin Boundary-Axis Expansion Audit

## Purpose

M808 audits M807 before any further low-margin corpus mining or active-steer
calibration.

The question is:

```text
Does M807 justify another retargeting/calibration step, or has the current
low-margin source-diverse corpus branch reached a synthesis point?
```

This milestone is audit-only:

```text
no replay
no residual calibration
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Evidence Audited

M807 implemented a clean no-training boundary-axis expansion:

```text
run dir: runs/m807_v4_low_margin_boundary_axis_expansion
anchor_rows: 136
initial_plan_rows: 6240
axis_plan_rows: 7882
axis_replay_rows: 7882
reconstruction_failures: 589
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

M807 covered the intended axes:

```text
bracketed_obstacle_distance
bracketed_obstacle_half_width
obstacle_lateral_offset
fault_severity
fault_activation_step
obstacle_half_width
source_step_neighborhood
```

The actor contract remained unchanged:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

## Key Result

M807 found `252` raw primary-window rows, but all of them came from the same
retarget axis:

```text
obstacle_half_width raw accepted rows: 252
all other axes raw accepted rows: 0
```

Raw accepted-row diversity:

```text
raw_unique_accepted_seeds: 3
required: 8

raw_unique_accepted_source_indices: 9
required: 8

raw_unique_accepted_fault_family_pairs: 4
required: 4

raw_unique_accepted_retarget_axes: 1
required: 3

raw_max_accepted_seed_dominance: 0.428571
required <= 0.25

raw_max_accepted_fault_pair_dominance: 0.714286
required <= 0.40

raw_max_accepted_retarget_axis_dominance: 1.0
required <= 0.60
```

The balanced export has only `48` rows because the M806 per-axis cap prevents
one axis from filling the corpus alone:

```text
accepted_axis_balanced_rows: 48
required: 80

unique_accepted_retarget_axes: 1
required: 3
```

Therefore M807 is correctly classified as:

```text
v4_low_margin_boundary_axis_expansion_geometry_only_diagnostic
```

## Why This Is Not A Tooling Failure

M807 did not fail because the tool only replayed half-width candidates. It
replayed thousands of rows across all planned axis families:

```text
bracketed_obstacle_distance reconstructed rows: 2276
bracketed_obstacle_half_width reconstructed rows: 1504
obstacle_lateral_offset reconstructed rows: 1360
fault_severity reconstructed rows: 870
fault_activation_step reconstructed rows: 804
source_step_neighborhood reconstructed rows: 227
```

The added axes created collision and safe outcomes, but their nearest positive
margins stayed outside the strict primary band:

```text
bracketed_obstacle_distance min positive margin: 0.000063175
bracketed_obstacle_half_width min positive margin: 0.000744491
fault_severity min positive margin: 0.000575566
source_step_neighborhood min positive margin: 0.005155853
fault_activation_step min positive margin: 0.011166531
obstacle_lateral_offset min positive margin: 0.021813194
```

The source-step reconstruction failures are expected under the exact-snapshot
requirement and current snapshot stride. They do not create accepted rows and
do not explain the half-width-only accepted set.

## Supported Claims

M808 supports these claims:

1. M807 is a clean no-training diagnostic run.
2. Multi-axis retargeting was actually exercised.
3. The strict primary low-margin band is reachable under current public
   anchors, but only through obstacle-half-width geometry retargeting.
4. The current M800-M807 branch does not yet provide a fair source-diverse,
   axis-diverse guard corpus for active-steer calibration.
5. Treating M804/M807 half-width rows as a pass would be a metric artifact and
   would invite objective overfit.

## Falsified Claims

M808 rejects the following claim for the current branch:

```text
The M806 boundary-axis expansion is enough to unblock active-steer calibration.
```

It also rejects:

```text
Another small retarget-axis tweak should be the default next step.
```

The branch has now tried:

```text
M800: strict low-margin source-diverse refresh design
M801: broad source refresh found no primary successful rows
M803/M804: boundary-window retarget created rows but only half-width geometry
M806/M807: multi-axis expansion still accepted only half-width geometry
```

That is enough local evidence to synthesize before more implementation.

## Failure Taxonomy

```text
scenario_sampling_failure:
  current public anchors do not expose source-diverse primary low-margin rows
  outside half-width geometry retargeting

metric_artifact:
  accepting the 252 raw half-width rows would pass the margin metric while
  failing the intended source and axis diversity evidence

objective_overfit risk:
  calibrating on the half-width-only rows would train the next objective to a
  narrow public geometry surface rather than a robust low-margin guard surface
```

Rejected labels:

```text
not contract_violation
not training_instability
not proof_washout
not promotion_gate_failure
```

## Decision

M808 does not admit active-steer calibration, residual calibration, PPO, or
promotion.

M808 also does not admit another narrow retargeting implementation on the same
branch. The next step should be a synthesis milestone:

```text
m809-v4-low-margin-source-diverse-branch-synthesis
```

The synthesis should decide whether to:

```text
continue with a new data-generation route,
pivot to active diagnostic history,
pivot to local terminal correction / QP-style repair,
or stop the low-margin retarget branch and reuse M804/M807 only as debug data.
```

## Next Blocker

```text
m809-v4-low-margin-source-diverse-branch-synthesis
```
