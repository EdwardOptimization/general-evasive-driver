# M1314 Paper-Route Source-History Corpus Expansion Design

## Summary

M1314 designs a larger source-history corpus after M1313 classified the current
fixed source-history surface as too narrow.

Decision:

```text
source_history_corpus_expansion_design_admit_plan_builder
```

The next step should not train a policy and should not tune another objective on
the same `38` pairs / `76` groups. It should first build a no-policy expansion
plan for a larger, more source-diverse response-history corpus.

## Motivation

The current corpus was enough to prove that fixed-current source-history
directionality is trainable, but it is now too small for robust evidence:

```text
M1309: simple weighting improved one split but regressed repeat robustness.
M1312: robust min-fold improved aggregate repeat but swapped pass surfaces.
M1313: primary failure type is scenario_sampling_failure.
```

The correct response is to increase source diversity and fold support before
another policy-side objective run.

## Corpus Expansion Goals

Target for the first expansion plan:

```text
planned_source_pairs >= 240
planned_pair_probe_groups >= 480
source_fault_family_count >= 6
corner_or_side_variant_count >= 16
onset_timing_bins >= 4
speed_bins >= 4
curvature_bins >= 3
pair_disjoint_folds: true
max_source_family_fold_share <= 0.40
max_probe_template_fold_share <= 0.55
pair_specific_weight_used: false
```

These are planning targets, not proof that the final materialized corpus will
all be accepted. The plan builder can later be followed by a no-policy
materialization smoke and an acceptance audit.

## Source Fault Families

The expansion should cover these source families:

| Family | Variants | Purpose |
| --- | --- | --- |
| Single-wheel grip collapse | FL, FR, RL, RR; transient and persistent | Sudden local tire authority loss |
| Tire blowout-like event | corner-specific drag, effective radius, friction drop | Extreme asymmetric response |
| Brake asymmetry | stuck caliper, partial brake loss, brake pull | Emergency braking authority asymmetry |
| Drive torque loss | left/right/rear drive loss, halfshaft-like failure | Throttle/yaw authority mismatch |
| Split-mu road | left-low/right-low, patch onset, recovery | Road-caused response asymmetry |
| Steering actuator fault | lag, rate limit, partial stuck angle | Command-response mismatch |
| Global friction step | high-to-low, low-to-high, mixed severity | Hidden envelope shift |
| Load / CG perturbation | mass, inertia, CG shift within simulator limits | Vehicle response variation |

If the current simulator cannot represent one family cleanly, the plan builder
should mark that family as `requires_source_generator_update` instead of forcing
fake labels.

## Scenario Axes

The plan should vary:

- entry speed: low, medium, high, extreme;
- road curvature: straight, mild curve, tight curve;
- obstacle timing: early, medium, late;
- obstacle lateral offset and width;
- road width / boundary margin;
- warm-up history length before emergency;
- fault onset timing relative to warm-up and obstacle;
- fault severity;
- sensor noise and actuator lag as materialization tags, not actor labels.

The goal is not random variety for its own sake. The goal is matched
source-history ambiguity:

```text
same or similar current observation;
different command-response history;
different correct emergency action.
```

## Materialization Rules

Actor-view observations must remain P0-compatible:

```text
72-dim human-view no-wheel frame + recurrent hidden state
```

Allowed in actor-view history:

- ego kinematics / IMU-like response;
- actuator state;
- previous physical commands;
- road/free-space/obstacle geometry in ego frame.

Forbidden in actor-view history:

- fault label;
- mu or friction map;
- tire force/slip/friction margin;
- brake scale, tire stiffness, actuator hidden parameters;
- feasibility labels;
- controller mode;
- TTC or oracle stopping distance;
- reference trajectory or path error.

Fault labels and source metadata are allowed only in planning, logging, fold
assignment, and offline diagnostics.

## Fold Discipline

The expansion plan must produce pair-disjoint folds:

```text
same physical source pair never appears in both train and eval for one repeat
split
```

Fold balancing should use group-level public metadata:

```text
source_family_pair
source_fault_pair
probe_template
corner_or_side_variant
onset_timing_bin
speed_bin
curvature_bin
margin_bucket
```

Forbidden:

```text
pair-id-specific weighting
history-intervention-specific weighting
private-holdout feedback
fold balancing using future policy success labels
```

## M1315 Plan Builder

M1315 should be a no-policy plan builder. It should not simulate trajectories
unless the existing source metadata already supports enumeration cheaply. The
goal is to create a deterministic expansion plan artifact.

Proposed command:

```bash
PYTHONPATH=src python -m autodrift.source_history_corpus_expansion_plan \
  --source-corpus-run-dir runs/m1273_four_wheel_source_corpus_export \
  --history-run-dir runs/m1280_four_wheel_source_response_history_materialization \
  --run-dir runs/m1315_source_history_corpus_expansion_plan \
  --target-source-pairs 240 \
  --fold-count 5
```

Required artifacts:

```text
runs/m1315_source_history_corpus_expansion_plan/summary.json
runs/m1315_source_history_corpus_expansion_plan/planned_source_pairs.csv
runs/m1315_source_history_corpus_expansion_plan/planned_pair_probe_groups.csv
runs/m1315_source_history_corpus_expansion_plan/fold_balance_summary.csv
runs/m1315_source_history_corpus_expansion_plan/family_coverage_summary.csv
```

If current source metadata is insufficient for a target family, the output must
include:

```text
requires_source_generator_update.csv
```

## Acceptance Criteria

M1315 should pass as infrastructure if:

```text
planned_source_pairs >= 240
planned_pair_probe_groups >= 480
source_fault_family_count >= 6
all_folds_nonempty: true
pair_disjoint: true
max_source_family_fold_share <= 0.40
pair_specific_weight_used: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
```

If the current source corpus cannot support those targets, M1315 should not fake
coverage. It should route to source-generator update design.

## Claim Limits

Allowed claim:

```text
M1314 defines a no-policy source-history corpus expansion plan.
```

Not allowed:

```text
policy performance improved;
closed-loop self-identification is proven;
PPO is admitted;
checkpoint promotion is admitted;
paper-level evidence is established.
```
