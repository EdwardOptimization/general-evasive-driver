# M797 V4 Active Steer Guard Calibration Design

## Purpose

M797 designs the next no-PPO residual calibration probe after M796 audited M795
as a clean near-miss negative.

The question is:

```text
Can an active/source-diverse low-margin steer guard make steering safety
lexicographic before intervention gap optimization?
```

This milestone is design-only:

```text
no implementation
no replay run
no optimizer run
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Why M795 Failed

M795 alpha `0.2` did two useful things:

```text
strict normal retention: pass
normal collision: 0
gap mean: 0.044080
M780 alpha 0.125 gap reference: 0.044047
```

But it failed the actual safety/coupling claim:

```text
active-source margin: +0.000003618
M786 alpha 0.15 active margin reference: +0.000028246

active normal steer gate:       0.668225
active intervention steer gate: 0.665187
active steer contrast:         -0.003038
```

The M795 objective treated the active guard as one weighted term inside a
single scalar loss. That was not enough. The next design must make active and
source-diverse low-margin steering safety a first-class feasibility condition.

## Actor Contract

The deployable actor contract does not change:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

Allowed deploy-time calibrator input:

```text
same deployable recurrent feature used by the frozen M761 residual head
```

Forbidden deploy-time inputs remain forbidden:

```text
mu
mass / CG / tire / brake / actuator hidden parameters
slip ratio or slip angle
tire force or friction margin
oracle feasibility labels
AEB/AES/drift-required labels
controller mode
TTC
reference trajectory
path error / heading error / curvature
success / collision / progress labels
terminal margin
fault family labels
source id
```

Training-time margins, source ids, intervention variants, and fault metadata
may only select rows, weight losses, or produce audit tables.

## Model

Keep the M795 calibrator family:

```text
SteerAttributedResidualGate(feature) -> [g_steer, 0.0, g_brake]
```

Base components remain frozen:

```text
base actor: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
residual head: runs/m761_v4_sequence_objective_probe/residual_head.pt
```

M798 may reuse the M795 code path but should add an explicit active-guard mode:

```text
--objective-mode active_steer_guard
```

The executed action remains:

```text
action = base_action + alpha * [
  g_steer * delta_raw_steer,
  0.0,
  g_brake * delta_raw_brake
]
```

## Guard Corpus

M798 should construct three training subsets.

### 1. Active Guard Rows

Always include the known binding active source:

```text
seed: 77025
source_index: 12
step: 24
```

This row is public and should not become the only guard.

### 2. Source-Diverse Low-Margin Normal Rows

Select source-diverse normal rows from existing public diagnostic artifacts,
using training-time metadata only:

```text
normal margin under full residual alpha 0.2 <= 0.00010
or normal margin under M795 alpha 0.2 <= 0.00005
```

Diversity constraints:

```text
min unique seeds: 8
min unique source_index values: 8
min unique fault-family pairs: 4
max single seed dominance: 0.25
```

If these constraints cannot be met from current artifacts, M798 should stop
before training and classify the run as requiring a low-margin corpus refresh.

### 3. Intervention Retention Rows

Use rows that carry intervention separation:

```text
hard_negative_available
large normal/intervention action gap
large normal/intervention margin gap
source-diverse positive rows
```

These rows retain steer and brake after the safety guard is satisfied.

## Training Structure

M798 should not train one undifferentiated loss from the start. Use a staged
lexicographic recipe.

### Stage A: Supervised Gate Separability Probe

Before closed-loop replay, verify that the deployable feature can at least fit
the desired gate labels on the selected tensor rows:

```text
low-margin normal:
  target g_steer <= 0.45
  target g_brake >= 0.80

intervention retention:
  target g_steer >= 0.80
  target g_brake >= 0.80
```

Pass criteria:

```text
active/source-diverse normal g_steer mean <= 0.55
intervention g_steer mean >= 0.70
intervention g_brake mean >= 0.70
normal/intervention steer contrast >= 0.15
```

If Stage A fails, do not claim an objective failure. Classify it as:

```text
deployable_feature_separation_failed
```

That would mean the current calibrator input cannot separate the needed cases,
and the branch should pivot to trajectory-time steering supervision or corpus
evidence.

### Stage B: Active-Steer Feasibility Projection

After each ordinary objective epoch, run a small projection pass on guard rows:

```text
minimize:
  relu(g_steer_normal - 0.45)^2
  + relu(0.80 - g_brake_normal)^2

until:
  active/source-diverse normal g_steer mean <= 0.55
```

This is not deploy-time oracle input. It is a training-time feasibility
restoration step over deployable features.

### Stage C: Gap Retention Under Guard

Only after Stage A/B pass should the objective optimize intervention gap:

```text
L_gap = relu(target_gap - calibrated_gap)^2
L_intervention_steer = relu(0.75 - g_steer_intervention)^2
L_intervention_brake = relu(0.75 - g_brake_intervention)^2
```

The guard remains active:

```text
L_guard = large_weight * relu(g_steer_low_margin_normal - 0.45)^2
```

Initial large weight:

```text
guard_weight: 50
```

This is intentionally much stronger than M795's soft guard.

## Exact Gates

M798 must evaluate the same alpha ladder:

```text
0.0, 0.125, 0.15, 0.2
```

Primary alpha:

```text
0.2
```

Strong candidate:

```text
strict normal retention passes
active-source margin >= M786 alpha 0.15 active margin
intervention gap mean >= M780 alpha 0.125 gap mean
source-diverse low-margin normal gate pass
active-source steer selectivity pass
```

Limited candidate:

```text
strict normal retention passes
active-source margin >= M786 alpha 0.15 active margin
intervention gap mean > M786 alpha 0.15 gap mean
source-diverse low-margin normal gate pass
active-source steer selectivity pass
```

Reference values:

```text
M780 alpha 0.125 gap mean: 0.044046541597
M786 alpha 0.15 gap mean: 0.043397390743
M786 alpha 0.15 active margin: 0.000028245983
```

Gate pass:

```text
active-source normal g_steer <= 0.55
active-source intervention g_steer >= 0.70
active-source steer contrast >= 0.15
source-diverse low-margin normal g_steer <= 0.55
intervention g_brake >= 0.70
```

## Required Artifacts

M798 should write:

```text
summary.json
alpha_metrics.csv
gate_metrics.csv
component_gate_metrics.csv
active_source_metrics.csv
low_margin_guard_rows.csv
separability_metrics.csv
training_metrics.csv
calibration_metrics.csv
replay_rows.csv
objective_rows.csv
rejected_rows.csv
calibrator.pt
```

## Failure Taxonomy

M798 should classify:

```text
v4_active_steer_guard_strong_candidate
v4_active_steer_guard_limited_candidate
v4_active_steer_guard_deployable_feature_separation_failed
v4_active_steer_guard_low_margin_corpus_blocked
v4_active_steer_guard_active_margin_failed
v4_active_steer_guard_no_gap_lift
v4_active_steer_guard_metadata_artifact
```

## Stop Conditions

Stop and audit before another objective if:

```text
1. source-diverse low-margin rows cannot be selected;
2. Stage A separability fails;
3. Stage B satisfies gate metrics but closed-loop active margin still fails;
4. Stage C improves gap by sacrificing guard metrics;
5. any candidate appears.
```

Any candidate still requires M799 audit before PPO or promotion.

## Decision

M797 admits:

```text
m798-v4-active-steer-guard-calibration-implementation
```

M798 may implement and run this no-PPO diagnostic only. It must not mutate the
base actor or M761 residual head, run PPO, or promote a checkpoint.
