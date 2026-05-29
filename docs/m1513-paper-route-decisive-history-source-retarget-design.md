# M1513 Paper-Route Decisive History Source Retarget Design

## Summary

M1513 designs a bounded public source-retarget route after M1512 found the
first M1511 source traces too safe for candidate materialization.

Decision:

```text
decisive_history_source_retarget_design_admit_implementation
```

This milestone is design only. It does not run retargeted rollouts,
materialize candidates, export a training corpus, run replay, run PPO, train,
promote, use private holdout, change actor inputs, or claim level3
self-identification.

## Why Retarget

M1511 proved fixed-policy trace plumbing works:

```text
six source families reached reveal, decision, and post-decision windows;
trace_row_count = 525;
guardrail_violation_count = 0.
```

M1512 blocked direct materialization:

```text
minimum trace margin = 4.170 m;
default T5 near-pass upper bound = 0.03 m;
five of six source families sampled aeb_feasible labels;
no wrong/delayed/current-tiled intervention margins were measured.
```

The next step is not training. The next step is to retarget the public source
families so the fixed policy runs closer to the boundary.

## Design Goal

The retarget route should answer:

```text
Can a small, source-diverse, public retarget grid reduce M1511 margins and
increase non-aeb label diversity while preserving the P0 actor contract?
```

It should not answer:

```text
Does the policy use history?
Can we materialize T4/T5 candidates?
Is the checkpoint promotable?
```

Those require measured interventions and candidate audits later.

## Retarget Axes

Retargeting may modify simulator hook specs only. It may use labels and
privileged simulator fields for sampling and diagnostics, but never as actor
inputs.

Allowed axes:

```text
obstacle distance:
  move obstacle closer with bounded scale factors.

obstacle half width:
  widen obstacle to reduce clearance margin.

speed range:
  increase initial speed within env stability limits.

friction / capability:
  lower mu, lower brake_scale, lower tire stiffness, or increase actuator tau.

perception reveal timing:
  reveal obstacle later, while recording the updated reveal and decision steps.

label sampling:
  use allowed_labels or threshold filters for public scenario generation only;
  labels_enter_actor_input must remain false.
```

Forbidden axes:

```text
actor observation changes;
hidden-parameter actor inputs;
TTC / required clearance / oracle feasibility actor inputs;
private holdout tuning;
unbounded random search;
candidate materialization inside the retarget smoke.
```

## Proposed Retarget Modes

M1514 should implement deterministic retarget modes, for example:

```text
close_wide:
  distance_range *= 0.65 to 0.80
  half_width_range += 0.35 to 0.65

low_mu_close:
  mu_range upper bound <= 0.65
  distance_range *= 0.75

late_reveal_high_speed:
  perception_reveal_step += 4 to 8
  speed_range += 2 to 4 m/s where source family permits

wide_low_brake:
  half_width_range += 0.45 to 0.80
  brake_scale_range upper bound <= 0.85

drift_required_focus:
  allowed_labels prefers aes_feasible / drift_required / unavoidable
  no actor-input label exposure
```

The implementation can start with four modes per source family. It should keep
the grid small:

```text
seed_count: 1
source_family_count: 6
retarget_modes_per_family: <= 4
max_specs: <= 24
max_rollout_steps: 128
checkpoint: M1362 alpha 0.1
```

## Artifact Contract

M1514 should write:

```text
retarget_spec_rows.csv
retarget_trace_rows.csv
retarget_snapshot_rows.csv
retarget_source_family_summary.csv
retarget_guardrail_summary.csv
summary.json
```

Each retarget row should include:

```text
source_family
retarget_mode
base_candidate_id
retarget_candidate_id
seed
base_distance_range
retarget_distance_range
base_half_width_range
retarget_half_width_range
base_speed_range
retarget_speed_range
base_mu_range
retarget_mu_range
base_brake_scale_range
retarget_brake_scale_range
base_reveal_step
retarget_reveal_step
labels_enter_actor_input
```

The summary should compare against M1511 baseline margins:

```text
baseline_min_margin_by_source_family
retarget_min_margin_by_source_family
margin_reduction_by_source_family
global_min_margin
non_aeb_label_source_family_count
near_boundary_proxy_count
guardrail_violation_count
```

## Public Smoke Acceptance

M1514 should not require full candidate acceptance. It should require evidence
that retargeting moves in the right direction.

Pass conditions:

```text
all six source families attempted;
all artifacts written;
guardrail_violation_count == 0;
candidate_materialized == false;
training/replay/PPO/promotion/private holdout remain false;
at least one retargeted trace reaches reveal and decision;
source-family failure reasons are explicit.
```

Evidence-quality targets:

```text
global_min_margin < 1.0 m, or at least 75% reduction vs M1511 global min;
at least two source families reduce min margin by >= 50%;
at least two source families sample non-aeb labels, or all failures are
  explicitly classified as retarget-too-hard / sampling failure.
```

Failing these targets is acceptable if it is recorded as source-retarget
evidence and routes to repair. The key is to avoid treating a high-margin
retarget smoke as candidate evidence.

## Next Milestone

Next:

```text
m1514-paper-route-decisive-history-source-retarget-implementation
```

M1514 should implement the bounded retarget spec generator and run a small
public smoke through the existing fixed-policy runner. It should still block
candidate materialization. If M1514 produces near-boundary traces, the next
step should audit those traces before measured intervention materialization.
