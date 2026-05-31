# M2059 Paper-Route Outcome-Supported Decisive Task Distribution Design

- status: completed
- decision: `outcome_supported_decisive_distribution_design_admit_no_rollout_candidate_generation`
- branch: `paper_route_outcome_supported_decisive_task_distribution`
- parent synthesis: `docs/m2058-paper-route-controlled-routing-smoke-task-quality-repaired-measured-execution-synthesis.md`
- reset/rollout/measured execution in M2059: `false`
- policy actions executed in M2059: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2059 replaces the offtrack-dominated repaired routing-smoke panel with a new
distribution route where outcome support is a precondition for full
controller-family comparison.

The goal is not to make GRU win. The goal is to produce decisive, source-diverse
tasks where L0/L1/L2/L3 can be compared fairly under the same deployable
actuator-level contract.

## Non-Negotiable Contract

All future task candidates must preserve:

```text
actor inputs:
  ego kinematics / IMU-like response;
  steering, throttle, brake actuator state;
  previous physical commands;
  ego-frame road/free-space/obstacle geometry;
  finite-window history or recurrent hidden state.

actor outputs:
  [steer_command, throttle_command, brake_command]
```

No actor may receive:

```text
mu, mass, CG, tire stiffness, brake scale, actuator tau;
slip ratio/angle, tire forces, friction margin;
oracle feasibility, AEB/AES/drift labels, controller mode;
reference path, TTC, required clearance, stopping distance;
collision/success/progress labels or any precomputed answer.
```

Generated rows remain:

```text
materialization_semantics=smoke_proxy
paper_validity_claim=false
```

until a later task-semantics validation branch explicitly upgrades them.

## Task Families

The new source-generation route must cover five paper-route families:

```text
T1_reactive_active_safety:
  ordinary reactive evasive driving where current response may be enough.

T2_same_current_different_older_history:
  matched current scene/current ego response with different older command-response evidence.

T3_active_diagnostic_warmup:
  low-risk warmup/diagnostic response before obstacle reveal.

T4_variable_diagnostic_delay:
  variable delay between useful response evidence and emergency decision.

T5_terminal_boundary_near_constraint:
  near-boundary avoidance where terminal margin, not just success count, matters.
```

## Candidate Quotas

M2060 should generate a no-rollout candidate artifact with `240` source
candidates:

```text
T1_reactive_active_safety: 48
T2_same_current_different_older_history: 60
T3_active_diagnostic_warmup: 60
T4_variable_diagnostic_delay: 36
T5_terminal_boundary_near_constraint: 36
```

Split:

```text
public_debug: 144
public_gate: 96
private_holdout: 0
```

Private holdout remains `0` in this branch until reset/materialization and
outcome-support smoke gates are stable. A later promotion branch must create a
fresh private holdout before paper-level claims.

## Difficulty Ladders

Each family should generate candidates across these difficulty axes:

```text
obstacle_distance_band:
  early, medium, late

road_width_band:
  generous, nominal, tight

curvature_band:
  straight_or_low, moderate, high

dynamics_band:
  nominal_mu, low_mu, mixed_mu, actuator_delay

initial_speed_band:
  low, nominal, high
```

The first generated artifact is a candidate/source panel, not an executed
benchmark. Geometry and dynamics should be diverse enough to support later
calibration, but not tuned to one controller profile.

## Outcome-Support Gates Before Full Comparison

No full 12-profile comparison is allowed until a smaller measured smoke
demonstrates outcome support.

Sentinel profiles for the smoke gate:

```text
L0_current_masked
L1_one_step
L2_window_50
L3_online_gru
L3_reset_control_corrected
```

Candidate panel smoke gates:

```text
global_success_rate >= 0.08
global_success_rate <= 0.60
global_offtrack_rate <= 0.80
global_collision_rate <= 0.25
each family success_count >= 6
each family success_source_count >= 3
each family profiles_with_success >= 2
max single source share of successes <= 0.25
generated_proxy success/offtrack distribution not worse than original rows by more than 0.20 offtrack rate
```

These thresholds are deliberately not paper claims. They are go/no-go gates for
whether a panel is worth full comparison.

## Full Comparison Gate

Only after the smoke gate passes may the branch scale to the full 12-profile
matrix:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L2_window_13_current_tiled
L2_window_25_current_tiled
L2_window_50_current_tiled
L2_window_100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

The full matrix must report:

```text
success, collision, offtrack, spin;
clearance-margin mean and lower tail;
first-critical action quality when available;
source diversity;
profile/source/family support;
parameter count and inference cost if model comparisons become paper-facing.
```

## Route

M2060 should implement only the no-rollout candidate generator:

```text
src/autodrift/paper_route_outcome_supported_decisive_task_candidates.py
tests/test_paper_route_outcome_supported_decisive_task_candidates.py
configs/paper_route_outcome_supported_decisive_task_candidates_v0.json
```

M2060 must not reset environments, execute rollouts, run measured execution,
train, rank controllers, or claim paper-level results.

Expected M2060 pass gates:

```text
candidate_count: 240
family quotas: 48 / 60 / 60 / 36 / 36
split quotas: public_debug 144 / public_gate 96 / private_holdout 0
difficulty-axis coverage present for all families
actor input forbidden-key count: 0
generated rows paper_validity_claim=true count: 0
profile_specific_tuning count: 0
guardrail_violation_count: 0
```

## Rejected Routes

Rejected:

```text
repair M2048 again:
  repeated offtrack dominance makes this a local-search trap.

full 12-profile measured execution immediately:
  outcome-support smoke gate must pass first.

claim L3 advantage from M2056:
  support is sparse and task-quality dominated.

high-fidelity simulator migration:
  current-sim task-distribution support is still unresolved.
```

## Next

Next milestone:

```text
m2060-paper-route-outcome-supported-decisive-task-candidate-generation
```
