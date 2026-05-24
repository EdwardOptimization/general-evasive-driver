# M721 Temporal Action-Boundary Outcome Mining Design

## Purpose

M721 turns the current coverage concern into a registered no-training mining
plan.

The working hypothesis is:

```text
M719 did find real temporal command-response action coupling, but the scenarios
were not close enough to collision or boundary margins for those action
differences to affect closed-loop outcome.
```

This milestone is design-only:

```text
no implementation
no data wave
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

It admits only a no-training M722 miner.

## Background

M716 already broadened current-model/proxy extreme hidden conditions:

```text
scenario_count:            16896
snapshot_count:            72056
matched_pair_count:         4096
reset_only_rows:              58
wrong_history_action_critical_rows: 0
result_class: cross_fault_reset_only
```

The current single-track model covered vehicle-level and axle-level faults:

```text
global mu drops
front/rear lateral authority drops
brake authority drops
drive authority drops
steering lag/rate/authority faults
mass / CG / inertia shifts
actuator delay proxies
combined capability faults
```

It also registered future-only high-fidelity faults:

```text
true single-wheel grip collapse
true single-wheel puncture or blowout
true left/right split-mu
true stuck-caliper or single-wheel brake pull
true asymmetric half-shaft torque loss
per-wheel ABS or brake-pressure faults
wheel-speed sensor drop or bias
steering pull from asymmetric front damage
tire-temperature or load-transfer asymmetric fault
suspension corner damage
```

M719 then tested temporal interventions on the same v2 family:

```text
temporal_action_critical_rows:  3114
temporal_outcome_critical_rows:    0
reset_action_critical_rows:     3140
reset_outcome_critical_rows:       0
normal_history_retention_pass:  true
result_class: temporal_action_only
```

The dominant variant was:

```text
mismatch_zero_command_history:
  action-critical rows: 3064
  action distance mean: 0.021019
  action distance max:  0.036131
  margin gap max:       0.006888
```

M720 classified that as strong action-level temporal coupling but not
closed-loop self-identification proof.

## Interpretation

The current negative result does not mean the actor ignores history. It means:

```text
the current scenario distribution did not expose enough near-boundary outcomes.
```

The next experiment should therefore not simply add more fault names. It should
create a targeted boundary miner that asks:

```text
when the actor changes action because command history is corrupted, can local
scenario sharpening make that action difference decide clearance or success?
```

This is the right level for the user's coverage concern. A complete extreme
data wave should include blowout, grip-loss, half-shaft, split-mu, brake-pull,
and steering-damage concepts, but the current proof blocker is outcome
conversion. M722 should first mine outcome boundaries inside the existing
current-model/proxy fault family, then use the result to decide whether the
next branch needs a four-wheel or explicit-yaw-disturbance dynamics upgrade.

## Source Selection

M722 should start from:

```text
runs/m719_temporal_action_response_mismatch/temporal_critical_rows.csv
runs/m719_temporal_action_response_mismatch/source_rows.csv
runs/m719_temporal_action_response_mismatch/intervention_rollouts.csv
configs/extreme_fault_coverage_v2_scenarios.json
```

Primary source rows:

```text
variant == mismatch_zero_command_history
temporal_action_critical == true
normal_success == true or normal_margin >= 0
first_action_distance_from_normal >= 0.015
```

Secondary source rows:

```text
variant in {reset_hidden, delayed_hidden_20, pre_fault_stale_hidden}
action_critical == true or temporal_action_critical == true
normal_success == true or normal_margin >= 0
```

Sentinel source rows:

```text
M719 rows with low action distance and healthy normal margins
M716 rejected rows with no temporal sensitivity
```

Sentinels are required so the miner does not report boundary-positive rows
everywhere.

## Source Balance

M719 accepted action rows were concentrated in early seeds because `max_pairs`
filled quickly. M722 must not simply take the first rows in CSV order.

Use source-balanced sampling over:

```text
seed
preferred_fault_family
wrong_fault_family
preferred_fault_severity
source_pool
step bucket
normal_margin bucket
action_distance bucket
```

Target before local perturbation:

```text
source_candidate_rows:       256-1024
unique_seeds:                >= 20 when available
unique_fault_families:       >= 5
max fault-family dominance:  <= 0.40
heldout split retained from source rows
```

If the existing M719 row set cannot satisfy these targets, M722 should write
the diversity failure explicitly rather than silently lowering the claim.

## Boundary Perturbation Axes

M722 should rerun scenarios in memory, as M719 did. CSV rows alone do not store
enough state to safely construct new interventions.

For each source row, evaluate a small local grid:

```text
decision snapshot step:
  step_offset in {-8, -4, 0, +4, +8}

obstacle timing / longitudinal placement:
  obstacle_x_shift_m in {-12, -8, -4, 0, +4}
  or the equivalent structured obstacle spawn/timing parameter

obstacle lateral placement:
  obstacle_y_shift_m in {-0.75, -0.50, -0.25, 0, +0.25, +0.50, +0.75}

obstacle footprint:
  half_width_delta_m in {0, +0.10, +0.20}
  half_length_delta_m in {0, +0.25}

road / free-space slack:
  boundary_slack_delta_m in {0, -0.25, -0.50}

fault activation timing for surprise faults:
  activation_step_delta in {-10, -5, 0, +5, +10}
```

Implementation must use structured environment or scenario fields after
inspection. Do not mutate serialized strings or inject oracle labels into actor
observations.

## Intervention Variants

At minimum, M722 should evaluate:

```text
normal
reset_hidden
mismatch_zero_command_history
delayed_hidden_20
pre_fault_stale_hidden
```

Optional if available:

```text
mismatch_response_delay_10
cross_fault_wrong_hidden
```

The current actor observation at the decision step must remain human-view:

```text
ego response
actuator state
previous physical commands
ego-frame road/free-space/obstacle geometry
recurrent hidden state
```

Forbidden actor inputs remain forbidden:

```text
mu / mass / tire / brake / actuator hidden parameters
fault labels
oracle feasibility
controller mode
speed_ref / beta_target
path error / heading error / path curvature
TTC / required clearance / oracle stopping distance
success / collision / progress labels
```

Obstacle and fault metadata may be used only for generation, logging, balancing,
and audit.

## Row-Level Acceptance

A candidate is outcome-critical only if normal history is viable:

```text
normal_success == true or normal_margin >= 0
```

and the intervention is both action-sensitive and outcome-sensitive:

```text
first_action_distance_from_normal >= 0.015
and one of:
  success_drop_from_normal == true
  margin_gap_from_normal >= 0.02
```

Do not accept rows where:

```text
normal history already fails
all variants fail
all variants succeed with negligible margin gap
the accepted result depends only on impossible obstacle placement
the actor observation contract changes
```

## Run-Level Classification

M722 should classify the result as one of:

```text
temporal_outcome_boundary_positive:
  accepted temporal outcome-critical rows are source-diverse and normal-history
  retention passes.

temporal_action_only_boundary_sparse:
  action deltas remain, but accepted outcome rows are below threshold or too
  concentrated.

normal_failed_too_severe:
  local perturbations mostly create impossible normal-history cases.

boundary_miner_artifact:
  outcome rows depend on malformed environment mutation, actor input leakage,
  or sentinel rows also becoming positive at high rate.

boundary_miner_empty:
  no meaningful boundary candidates are found.
```

## Run-Level Acceptance Thresholds

For a source-positive M722 result:

```text
accepted_rows >= 30
temporal_outcome_critical_rows >= 20
unique_fault_families >= 4
unique_seeds >= 10
max_fault_family_dominance <= 0.40
normal_history_retention_pass == true
sentinel_false_positive_rate <= 0.05
actor_parameters_changed == false
training_started == false
optimizer_started == false
ppo_used == false
promoted == false
```

The `unique_seeds >= 10` threshold is deliberately lower than M716's generic
coverage target because M719's action-critical temporal rows used only `22`
unique temporal seeds after `max_pairs` saturation. If source balancing exposes
more seeds, the implementation should report the larger count.

## Required Artifacts For M722

M722 should write:

```text
runs/m722_temporal_action_boundary_outcome_miner/summary.json
runs/m722_temporal_action_boundary_outcome_miner/source_rows.csv
runs/m722_temporal_action_boundary_outcome_miner/candidate_variants.csv
runs/m722_temporal_action_boundary_outcome_miner/intervention_rollouts.csv
runs/m722_temporal_action_boundary_outcome_miner/accepted_rows.csv
runs/m722_temporal_action_boundary_outcome_miner/rejected_rows.csv
runs/m722_temporal_action_boundary_outcome_miner/variant_summary.csv
runs/m722_temporal_action_boundary_outcome_miner/fault_family_summary.csv
docs/m722-temporal-action-boundary-outcome-miner-implementation.md
```

The summary must include:

```text
scenario_count
source_candidate_rows
candidate_variant_count
accepted_rows
temporal_action_critical_rows
temporal_outcome_critical_rows
normal_failed_rejected
history_insensitive_rejected
sentinel_false_positive_rows
unique_fault_families
unique_seeds
max_fault_family_dominance
normal_history_retention_pass
result_class
actor_parameters_changed
training_started
optimizer_started
ppo_used
promoted
```

## M722 Command

M722 should implement and run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.temporal_action_boundary_outcome_miner \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --temporal-rows runs/m719_temporal_action_response_mismatch/temporal_critical_rows.csv \
  --seed-start 72000 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m722_temporal_action_boundary_outcome_miner
```

A tiny implementation smoke is acceptable for debugging, but M722's result
classification must come from the registered run or a separately registered
scale change.

## Supported Claims

M721 supports:

```text
1. The current missing evidence may be boundary mining, not absence of temporal
   command-response coupling.

2. A complete extreme scenario data wave should be source-balanced and
   boundary-aware, not only fault-name-rich.

3. True single-wheel and asymmetric drivetrain failures remain important, but
   they require a higher-fidelity dynamics branch before they can support
   physical claims.

4. M722 can test the near-boundary explanation without changing actor inputs or
   training the policy.
```

## Falsified Claims

M721 falsifies:

```text
1. M719 action-only rows can be exported directly as source-positive self-ID
   proof.

2. The next highest-leverage step is naked PPO.

3. Another broad fault-list expansion without outcome-boundary mining is enough
   to resolve the current blocker.

4. Per-wheel blowout, split-mu, brake-pull, and half-shaft failures can be
   claimed as physically represented by the current single-track model.
```

## Next Step

M722 should implement the no-training temporal action-boundary outcome miner
and classify the result before any source export, objective update, PPO, model
promotion, or dynamics-fidelity branch.
