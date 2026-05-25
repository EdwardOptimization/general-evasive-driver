# M823 V4 Adaptive Primary Calibration Next Route Design

## Purpose

M823 chooses the next evidence route after M821/M822 closed fixed scalar/vector
residual-gate tuning on the M814/M817 corpus.

The design question is:

```text
What should the project do after identity is the best fixed gate?
```

M823 is design-only:

```text
no implementation
no replay
no calibrator training
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Starting Point

M821/M822 established:

```text
fixed scalar/vector candidates evaluated: 53
normal exact replay rows: 4505
intervention exact replay rows: 13515
selected candidate: identity
best nonidentity p05 margin lift: negative on train and holdout
actor checksum changed: false
M761 residual-head checksum changed: false
```

The fixed-gate route is closed for this corpus:

```text
do not continue scalar/vector residual suppression on M814/M817 rows
do not train a learned adaptive gate from an identity-only result
do not start PPO
do not promote
```

## Route Options

### Option A: Continue Fixed-Gate Calibration

Rejected.

Reason:

```text
M821 already evaluated identity, scalar gates, vector gates, and template gates.
Identity ranked first. Repeating the same grid on the same corpus would optimize
public rows without adding evidence.
```

### Option B: Train A Learned Adaptive Gate

Rejected for now.

Reason:

```text
M817 showed near-identity retention only.
M821 showed no fixed-gate margin-lift signal.
There is no clean target showing what the learned gate should do.
```

A learned gate should only return after a new data route or objective creates a
nontrivial train/holdout signal.

### Option C: Residual-Necessity Diagnostic

Useful, but not first.

A no-training diagnostic could ask whether M761 residuals are necessary by
ablating residual components per row. But M821 already suggests residual
suppression hurts low-margin robustness. The stronger missing evidence is not
"which residual scalar is best"; it is whether the project has enough diverse
hidden-dynamics situations where history matters.

### Option D: Extreme Hidden-Dynamics Data Route

Selected.

This route directly addresses the current research goal:

```text
find scenarios where the same apparent emergency geometry requires different
actions because hidden vehicle capability changed, and where wrong/reset/delayed
command-response history degrades margin or action quality.
```

This is a better next route because it adds new evidence instead of tuning the
same public proof rows.

## Selected Route

Decision:

```text
pivot_to_extreme_hidden_dynamics_data_route_design
```

The next design should create an extreme hidden-dynamics data route, not another
residual-gate calibrator.

The route should mine:

```text
matched-current-state / action-divergent cases
wrong-history sensitive cases
reset-hidden sensitive cases
delayed-response sensitive cases
zero-command-history sensitive cases
near-boundary normal-success cases
mitigation-only cases where avoidance is impossible but margin loss differs
```

## Fault Coverage Boundary

The current single-track model can represent or proxy these families:

```text
global_mu_drop
front_lateral_authority_drop
rear_lateral_authority_drop
brake_authority_drop
drive_authority_drop
steering_fault
mass_cg_shift
delay_noise_fault
combined_fault
```

It cannot honestly claim true wheel-level faults:

```text
true single-wheel blowout
true left/right split-mu
true stuck single caliper
true halfshaft/CV asymmetry
true suspension corner damage
true wheel-speed sensor faults
```

Those may be represented only as current-model proxy faults until a four-wheel
or high-fidelity dynamics engine exists.

The next route must preserve this claim boundary in docs and artifacts.

## Evidence Targets

The next route should optimize for evidence, not immediate training:

```text
source-diverse hidden-dynamics pairs
fault-family diversity
onset-time diversity
warm-up-mode diversity
obstacle timing/lateral diversity
history-intervention sensitivity
action divergence under matched apparent state
normal-history margin advantage over wrong/reset/delayed history
```

Candidate row categories:

```text
primary_self_id_row:
  normal history succeeds or has higher margin;
  wrong/reset/delayed history loses margin or collides;
  source/fault/onset diversity passes.

matched_action_divergent_row:
  apparent current state and obstacle geometry are close;
  fault family differs;
  selected action or first action prefix differs materially.

mitigation_row:
  all variants collide or fail strict success;
  normal history still improves margin or impact proxy.
```

## Proposed Gates For M824 Design

M824 should design the concrete data route with gates such as:

```text
accepted primary self-ID rows >= 120
unique seeds >= 16
unique source groups >= 48
unique fault-family pairs >= 8
unique onset buckets >= 4
unique warm-up modes >= 3
max seed dominance <= 0.20
max fault-family-pair dominance <= 0.30
normal-vs-wrong margin gap >= 0.01 for accepted rows
normal-vs-reset or delayed gap retained on holdout split
actor and residual checksums unchanged
no PPO
no promotion
```

M824 should not weaken these into a single aggregate success metric.

## Output Direction

The next implementation after M824 should produce:

```text
summary.json
source_rows.csv
matched_pair_rows.csv
history_intervention_rows.csv
accepted_self_id_rows.csv
rejected_rows.csv
diversity_summary.json
gate_summary.csv
```

It should also explicitly mark:

```text
fidelity_class: current_model_fault | current_model_proxy | future_only
```

No deploy-time actor input may include fault labels, hidden parameters, or
oracle feasibility labels.

## Decision

Decision:

```text
admit_extreme_hidden_dynamics_data_route_design
```

Next blocker:

```text
m824-v4-extreme-hidden-dynamics-data-route-design
```
