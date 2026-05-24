# M702 Boundary Sensitivity-Scale Diagnostic Audit

## Purpose

M702 audits the M701 `scale_sparse_plausible` result and decides whether the
trajectory-terminal-boundary source-mining branch should continue with more
fresh sampling tweaks.

This milestone is process-only:

```text
no rerun
no threshold relaxation
no source corpus export
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M701 was implementation-clean:

```text
actor_parameters_changed: false
training_started:         false
ppo_used:                 false
promoted:                 false
```

M701 covered:

```text
variants:                     32
episodes_attempted:        16384
snapshots_collected:      129792
perturbation_evaluated:    26112
```

Aggregate result:

```text
result_class:                 scale_sparse_plausible
accepted_rows:                99
source_positive_variants:      0
history_action_critical_rows:  0
best_margin_sensitivity_p95:   0.009688
registered_threshold:          0.020000
```

Scale summary:

```text
scale              accepted trajectory history-critical result
local                     0          0                0 fresh_surface_empty
plausible                16         16                0 history_insensitive
stress                   21         21                0 history_insensitive
unrealistic_probe        62         62                0 history_insensitive
```

Window summary:

```text
target_obstacle_distance: 2.0, 1.0, 0.0, -1.0
max_prepass_margin:      0.50, 1.00
history_action_critical: 0 in every window
```

M694-M701 branch history:

```text
M695:
  inherited M692 source surface -> surface_empty

M698:
  fresh broad sampling -> 0 accepted rows

M701:
  broader window/scale ladder -> sparse accepted rows, all history-insensitive
```

The branch has now tested inherited proof rows, fresh broad sampling, closer
obstacle-distance windows, wider prepass windows, and larger action override
scales. None produced a source-positive self-identification surface.

## Supported Claims

The evidence supports:

```text
1. M701 is a valid diagnostic run and did not mutate the actor.

2. The current fresh/ood scenario distribution can generate sparse
   terminal-sensitive rows when action overrides are made larger.

3. Those sparse rows are not self-identification evidence because the
   history-action-critical count remains zero.

4. The current source-mining problem is unlikely to be solved by another small
   sampler/window/perturbation tweak on the same distribution.

5. The stronger hypothesis is scenario coverage failure: the project has not
   yet generated enough hidden-condition situations where online vehicle
   capability identification is necessary.
```

## Falsified Claims

The evidence falsifies:

```text
1. M698 was empty only because the first-action perturbation scale was too
   small.

2. Moving the target obstacle distance to 1.0, 0.0, or -1.0 is sufficient to
   reveal history-critical rows.

3. Stress or unrealistic action overrides alone can turn the current
   distribution into an objective-ready self-ID source surface.

4. Sparse accepted rows are enough to admit source-corpus export.
```

The evidence does not falsify:

```text
closed-loop self-identification as the long-term project objective
```

because the tested scenarios may simply not contain strong enough hidden
dynamics ambiguity.

## Failure Taxonomy Summary

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
The current scenario distribution does not produce source-positive
history-critical rows after the registered window and scale ladder.
```

Secondary:

```text
metric_artifact
```

Reason:

```text
M701 accepted rows are sparse and history-insensitive. Treating them as
self-identification evidence would optimize a metric artifact rather than a
causal command-response-history mechanism.
```

Not classified as:

```text
training_instability:
  no training occurred

proof_washout:
  actor parameters were unchanged

contract_violation:
  actor inputs were unchanged
```

## Public Gate Overfit Risk

The immediate overfit risk is no longer a single public proof row. It is a
process-level risk:

```text
keep changing source miners until one accepts rows from a distribution that
does not actually require self-identification
```

M701 shows why this is dangerous. Larger scales can create accepted rows, but
those rows remain history-insensitive. A gate-passing workflow could be fooled
by the accepted-row count unless it keeps the stronger self-ID requirement:

```text
source-positive rows must be history-action-critical and source-diverse
```

## Scenario Coverage Hypothesis

The user raised the most plausible missing factor:

```text
extreme hidden-condition scenarios may not be covered yet
```

Examples include sudden grip loss, tire failure, axle or drive loss, brake
faults, and other faults. M702 accepts this as the next branch hypothesis, with
one important modeling caveat.

Current AutoDrift dynamics are single-track / bicycle-style. They model:

```text
global friction mu
front/rear tire stiffness
mass and CG shift
drive and brake authority
steering and drive actuator time constants
```

They do not faithfully model:

```text
individual left/right wheel puncture
single-corner brake pull
true split-left/right mu yaw moments
true half-shaft asymmetry
```

Therefore the next branch should be staged:

```text
Stage A:
  implement current-model hidden capability faults and proxies that the
  single-track simulator can represent honestly

Stage B:
  if Stage A produces useful self-ID surfaces, plan a four-wheel dynamics
  extension or higher-fidelity engine for true single-wheel/asymmetric faults
```

## Extreme Hidden-Condition Scenario Families

M703 should design a no-training scenario corpus around hidden faults. Hidden
fault labels are allowed for scenario generation, logging, teacher/oracle
analysis, and audits, but must not enter actor inputs.

Current-model-compatible families:

```text
global_mu_drop:
  sudden or ramped loss of surface friction

front_lateral_authority_drop:
  front tire stiffness/capacity loss, understeer-heavy failure proxy

rear_lateral_authority_drop:
  rear tire stiffness/capacity loss, oversteer/drift-recovery failure proxy

brake_authority_drop:
  brake fade or reduced max brake force

drive_authority_drop:
  half-shaft/drive-loss proxy through reduced drive force

steering_authority_or_lag_fault:
  reduced steering response, increased lag, deadzone, or stiction proxy

mass_cg_load_shift:
  payload or CG shift that changes yaw/lateral authority

sensor_actuator_delay_noise:
  observation delay/noise/bias and actuator delay under emergency timing

combined_fault:
  paired moderate faults such as low mu plus brake fade, or rear authority
  loss plus steering lag
```

Future four-wheel / higher-fidelity families:

```text
single_wheel_grip_collapse
single_wheel_puncture_or_blowout
left_right_split_mu
stuck_caliper_or_single-wheel brake pull
true half-shaft asymmetric torque loss
wheel-speed / tire-temperature / load-transfer rich faults
```

## Corpus Requirements

The next corpus should not just be "hard scenarios." It should construct
matched hidden-condition ambiguity:

```text
same or matched current road/obstacle geometry
similar current ego state
different hidden capability/fault state
different safe emergency action or margin outcome
wrong history causes margin/success degradation
```

Candidate gates:

```text
normal-history success or positive margin
wrong-history or reset-history degradation
fault-vs-nominal action divergence
source diversity across seeds, fault families, speeds, obstacle timings
no actor input contract violation
```

Warm-up is important. The driver should experience the hidden condition before
the emergency:

```text
0.5s-2.0s pre-emergency driving/probing window
fault already active or activates during warm-up
obstacle appears after response evidence exists
GRU hidden persists into emergency
```

This matches the project goal: a driver-like policy infers capability through
its own commands and sensed vehicle response, not through hidden fault labels.

## Next Branch Decision

Synthesis decision:

```text
pivot
```

Close the active branch:

```text
trajectory_terminal_boundary_source_mining
```

Open the next branch:

```text
extreme_hidden_condition_scenario_generation
```

M703 should be design-only:

```text
m703-extreme-dynamics-scenario-corpus-design
```

M703 should not train. It should specify:

```text
fault schema
scenario generation stages
current single-track proxy limits
matched hidden-condition pair requirements
metrics and artifacts
acceptance/failure taxonomy
no-training/no-PPO/no-promotion guardrails
```

## Decision

M702 blocks:

```text
source corpus export from M701
objective actor update
PPO
checkpoint promotion
further same-distribution perturbation-scale tuning
```

Decision string:

```text
boundary_sensitivity_audit_pivot_to_extreme_hidden_condition_scenarios
```
