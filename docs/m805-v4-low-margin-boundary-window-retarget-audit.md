# M805 V4 Low-Margin Boundary-Window Retarget Audit

## Purpose

M805 audits M804 before any active-steer residual calibration, PPO, promotion,
or another retarget implementation.

The question is:

```text
Is M804 a usable source-diverse guard corpus, a clean geometry-only diagnostic,
or a tooling artifact?
```

This milestone is audit-only:

```text
no retarget rerun
no residual calibration
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Cleanliness Check

M804 preserved the no-training invariants:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
reconstruction_failures: 0
```

The final M804 artifacts are not explained by the earlier body/path frame
implementation issue. That issue was corrected before the final run by using
the snapshot obstacle's body-frame coordinates for relocation. The final run
reran closed-loop candidates and did not post-process margins.

## Primary-Window Result

M804 successfully populated the primary low-margin window:

```text
accepted_low_margin_window_rows: 252
accepted margin min: 0.000004953
accepted margin median: 0.000025013
accepted margin max: 0.000046264
```

This is a useful diagnostic. It falsifies the narrow claim that the
`0.0 <= margin <= 0.00005` window is unreachable in the current simulator.

Accepted rows also preserve the local intervention proof:

```text
intervention_success_rate: 0.0
intervention_collision_rate: 1.0
intervention margin max: -0.000175
```

So the rows are not merely successful normal rollouts; their source
interventions remain wrong-history sensitive.

## Why It Is Not a Guard-Corpus Pass

All accepted rows come from one retarget axis:

```text
obstacle_half_width accepted rows: 252
obstacle_distance accepted rows: 0
unique_accepted_retarget_axes: 1
max_accepted_retarget_axis_dominance: 1.0
```

Source diversity also fails:

```text
unique_accepted_seeds: 3
required: 8

unique_accepted_source_indices: 9
required: 8

unique_accepted_fault_family_pairs: 4
required: 4

max_accepted_seed_dominance: 0.428571
required <= 0.25

max_accepted_source_index_dominance: 0.142857
required <= 0.15

max_accepted_fault_pair_dominance: 0.714286
required <= 0.40
```

Accepted rows are concentrated in:

```text
seeds:
  78143: 108
  78096: 72
  78272: 72

fault-family pairs:
  front_lateral_authority_drop->combined_fault: 180
  combined_fault->delay_noise_fault: 39
  combined_fault->global_mu_drop: 21
  combined_fault->brake_authority_drop: 12
```

Therefore M804 must not admit active-steer residual calibration as if the
source-diverse low-margin guard corpus exists.

## Classification

M804 is classified as:

```text
v4_low_margin_boundary_window_geometry_only_diagnostic
```

Failure taxonomy:

```text
scenario_sampling_failure
metric_artifact risk if treated as a pass
objective_overfit risk if used as the only guard corpus
```

Rejected labels:

```text
not contract_violation
not training_instability
not proof_washout
not promotion_gate_failure
```

## Supported Claims

M805 supports:

```text
1. M804 is a clean no-training diagnostic run.

2. The primary low-margin band is reachable by closed-loop replay under public
   obstacle geometry retargeting.

3. The accepted rows preserve strong intervention sensitivity.

4. The accepted rows are not source-diverse or axis-diverse enough for the
   active-steer guard corpus.
```

## Falsified Claims

M805 falsifies:

```text
1. The strict primary low-margin threshold is impossible in the current
   simulator.

2. Fixed obstacle-distance deltas are sufficient to populate the primary
   low-margin window.

3. M804 admits active-steer calibration.

4. Geometry-only rows should be counted as a source-diverse guard pass.
```

## Decision

Do not run active-steer calibration, PPO, or promotion from M804.

Do not weaken source-diversity thresholds.

Do not treat the `252` geometry-only rows as the final guard corpus.

The right next step is a design milestone for source-diverse boundary-axis
expansion. It should keep the M804 tool's closed-loop replay discipline, but
add axes that can move more M801 diagnostic seeds and fault pairs into the
primary window without relying only on obstacle half-width:

```text
obstacle lateral offset retargeting
source-step retargeting / neighboring snapshot replay
fault activation step micro-sweeps
fault severity micro-sweeps
distance bisection instead of fixed deltas
axis-balance gates
```

The M804 geometry-only accepted rows may be retained as a limited diagnostic
debug corpus, but not as a calibration gate until an audit explicitly scopes
that use.

## Next Blocker

```text
m806-v4-low-margin-boundary-axis-expansion-design
```

M806 should design the source-diverse axis expansion. It remains no-training
design work; residual calibration, PPO, actor mutation, residual-head mutation,
and promotion remain blocked.
