# M809 V4 Low-Margin Source-Diverse Branch Synthesis

## Purpose

M809 synthesizes the M800-M808 low-margin source-diverse corpus branch before
another implementation milestone.

This is a workflow synthesis milestone:

```text
no replay
no residual calibration
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

The synthesis decision is:

```text
pivot
```

The current branch should stop trying narrow public retarget-axis tweaks. The
next work should open a new data-generation route that creates source-diverse
near-boundary evidence rather than repeatedly adjusting the same M801/M804
public anchors.

## Evidence Summary

### M800

M800 designed a strict low-margin source-diverse corpus refresh. It kept the
primary gate fixed:

```text
0.0 <= normal min_clearance_margin <= 0.00005
accepted rows >= 80
unique seeds >= 8
unique source indices >= 8
unique fault-family pairs >= 4
max seed dominance <= 0.25
max fault-pair dominance <= 0.40
```

The design explicitly rejected threshold relaxation and calibration from a
single low-margin public source.

### M801

M801 ran the broad source refresh:

```text
positive sequence outcomes: 4825
unique positive seeds: 108
unique positive fault-family pairs: 18
primary successful non-collision low-margin rows: 0
```

The broad wave improved source coverage but did not populate the primary
near-boundary successful band. This showed the problem was not simply "not
enough positives."

### M802

M802 audited M801 as a clean diagnostic-band-only result. It rejected weakening
the primary threshold after seeing the result.

### M803-M804

M803 designed boundary-window retargeting around collision-edge and safe-edge
anchors. M804 implemented it:

```text
anchor_rows: 136
retarget_replay_rows: 672
accepted_low_margin_window_rows: 252
accepted margin range: 0.000004953 to 0.000046264
```

M804 proved the primary margin band is reachable. But every accepted row came
from one geometry axis:

```text
obstacle_half_width accepted rows: 252
obstacle_distance accepted rows: 0
```

Accepted rows were also source-concentrated:

```text
unique seeds: 3
max seed dominance: 0.428571
max fault-pair dominance: 0.714286
```

### M805

M805 audited M804 as a clean geometry-only diagnostic. It accepted the useful
fact that the primary band is reachable, but rejected using those rows for
active-steer calibration.

### M806-M807

M806 designed a wider boundary-axis expansion. M807 implemented it and replayed
all intended axis families:

```text
axis_replay_rows: 7882
bracketed_obstacle_distance reconstructed rows: 2276
bracketed_obstacle_half_width reconstructed rows: 1504
obstacle_lateral_offset reconstructed rows: 1360
fault_severity reconstructed rows: 870
fault_activation_step reconstructed rows: 804
source_step_neighborhood reconstructed rows: 227
obstacle_half_width reconstructed rows: 252
```

M807 kept actor and residual-head checksums unchanged and did not train.

However, the primary-window accepted rows still came from only half-width:

```text
accepted_axis_raw_rows: 252
accepted_axis_balanced_rows: 48
raw_unique_accepted_retarget_axes: 1
raw_max_accepted_retarget_axis_dominance: 1.0
```

The nearest positive margins outside half-width remained above the primary
threshold:

```text
bracketed_obstacle_distance: 0.000063175
bracketed_obstacle_half_width: 0.000744491
fault_severity: 0.000575566
source_step_neighborhood: 0.005155853
fault_activation_step: 0.011166531
obstacle_lateral_offset: 0.021813194
```

### M808

M808 audited M807 as a clean no-training geometry-only diagnostic and routed
the branch to synthesis.

## Supported Claims

The branch supports these claims:

1. The strict primary low-margin band is not impossible under the current
   simulator and M568+M761 closed-loop replay.
2. Public geometry retargeting can create legitimate primary-window rows
   without changing actor or residual-head checksums.
3. The currently found primary-window rows preserve local diagnostic value, but
   only as a limited debug corpus.
4. Broad source refresh alone is insufficient to create primary successful
   near-boundary rows.
5. Narrow retarget-axis expansion around the current public anchors does not
   create source-diverse or axis-diverse low-margin evidence.

## Falsified Claims

The branch falsifies these working claims:

```text
More broad positive outcomes alone will populate the strict primary
low-margin successful band.
```

```text
Boundary-window retargeting around M801 anchors can produce a source-diverse
guard corpus.
```

```text
Adding lateral, source-step, fault-activation, fault-severity, and bracketed
distance/width retargeting is enough to unblock active-steer calibration.
```

```text
The M804/M807 half-width rows are sufficient evidence for a calibration or PPO
admission gate.
```

## Failure Taxonomy Summary

### scenario_sampling_failure

The current public source distribution has a near-boundary successful band only
on one geometry degree of freedom. It does not expose the source-diverse,
fault-diverse, axis-diverse surface needed for a fair low-margin guard corpus.

### metric_artifact

The margin metric alone looks positive because the primary band contains `252`
raw rows. That is misleading unless source and axis diversity are enforced.

### objective_overfit

Training or calibrating against the half-width-only rows would likely overfit a
public geometry surface instead of learning a robust low-margin safety guard.

Rejected failure labels:

```text
contract_violation
training_instability
proof_washout
promotion_gate_failure
```

The branch did not break the actor contract or wash out proof rows; it failed
to generate the right evidence distribution.

## Public Gate Overfit Risk

The overfit risk is high if the project keeps iterating on M801/M804 public
anchors. The observed pattern is stable:

```text
strict low-margin success exists
but it is explained by obstacle-half-width retargeting
not by source-diverse hidden-dynamics or history-sensitive boundary cases
```

Continuing to tune axes on the same anchors would optimize for passing the
public low-margin gate, not for discovering a general evasive-driving
self-identification mechanism.

Private holdout evidence was not used and must remain promotion-only.

## Next Branch Decision

Decision:

```text
pivot
```

The next branch should be:

```text
v4_low_margin_new_data_route
```

The next design milestone should not weaken the primary low-margin threshold
and should not calibrate from M804/M807 rows. It should design a new data route
with at least these requirements:

```text
1. generate source-diverse near-boundary normal rows before retargeting;
2. include active diagnostic history or warm-up maneuvers so history carries
   dynamics evidence before the emergency;
3. vary obstacle timing and fault activation jointly rather than only
   post-hoc obstacle geometry;
4. keep current-model proxy labels honest and avoid claiming true wheel-level
   faults before a higher-fidelity backend exists;
5. preserve the P0 human-view no-wheel actor contract;
6. block residual calibration, PPO, and promotion until the new corpus passes
   source, fault, and axis diversity gates.
```

The immediate next blocker is:

```text
m810-v4-low-margin-new-data-route-design
```

## Branch Closure

M809 closes the current branch:

```text
v4_low_margin_source_diverse_corpus_refresh
```

M804/M807 artifacts remain useful as limited debug data, but not as a
promotion, PPO, or active-steer calibration corpus.
