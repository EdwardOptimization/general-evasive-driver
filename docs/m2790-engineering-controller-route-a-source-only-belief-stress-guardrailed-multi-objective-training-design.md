# M2790 Engineering Controller Route A Source-Only Belief-Stress Guardrailed Multi-Objective Training Design

## Metadata

- status: completed
- decision: `admit_source_only_belief_stress_guardrailed_multi_objective_training_preflight`
- manifest: `experiments/manifests/m2790-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-design.json`
- design doc: `docs/m2790-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-design.md`
- parent synthesis: `docs/m2789-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-branch-synthesis.md`
- parent audit: `docs/m2788-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-delta-panel-result-audit.md`
- parent fresh-holdout summary: `runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel/summary.json`
- source checkpoint: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt`
- base candidate checkpoint: `runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt`
- follow-up manifest: `experiments/manifests/m2791-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-preflight.json`
- next: `m2791-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-preflight`

## Design Scope

M2790 is design-only. It admits a bounded M2791 guardrailed multi-objective
training/update preflight, but M2790 itself does not execute reset, step,
policy action, rollout, replay, validation, training, PPO, source build,
adapter probe, external simulation, ranking, winner selection, checkpoint
promotion, success-rate verdict computation, driver-performance measurement,
paper evaluation, high-fidelity validation, full-driver gate, or self-ID proof.

The purpose is to convert the M2789 synthesis decision into an executable
future evidence branch without converting source-only deltas into a result.
The design treats M2787 as diagnostic accounting, not as validation,
performance, ranking, or self-identification evidence.

## Parent Evidence

M2789 accepts M2786-M2788 as a complete claim-safe source-only belief-stress
fresh-holdout diagnostic branch:

```text
M2787 status_pass: true
M2787 required_artifacts_present: true
M2787 gate_matrix_pass: true
M2787 failed_gate_ids: []
fresh holdout seed indices: 4, 5, 6, 7
M2784 seed indices: 0, 1, 2, 3
fresh holdout disjoint from M2784: true
horizon steps: 120
M2784 horizon steps: 80
paired execution rows: 144
paired delta rows: 72
proof gates: 13
generalization holdout gates: 8
promotion guards: 4
actor guards: 7
mitigation guards: 8
claim rows: 11
gate rows: 25
```

The fresh-holdout directional evidence is mixed:

```text
road-margin deltas:
  positive rows: 72/72
  mean: 0.003045548777864837

yaw-rate deltas:
  lower rows: 60/72
  mean: -0.00017877287320032365

final-speed deltas:
  positive rows: 63/72
  mean: 0.0026159244394306303

obstacle-clearance deltas:
  positive rows: 43/72
  negative rows: 29/72
  mean: 0.00035927758389157286
  min: -0.0037394441382763155

throttle/brake conflict:
  zero rows: 72/72

mean action L1 delta:
  mean: 0.000330366297728483
```

This is enough to justify a new guarded training recipe. It is not enough to
promote the M2782 candidate or claim that it is better than the M2655 source.

## Route A Contract

M2791 must preserve the post-M2470 Route A engineering-controller contract:

```text
actor observation shape: 72
actor action shape: 3
action mapping: steer, throttle, brake
hidden/oracle actor input allowed: false
actor input feature addition allowed: false
role labels actor-visible: false
dynamics labels actor-visible: false
stress labels actor-visible: false
curriculum/admission labels actor-visible: false
outcome/progress/success/verdict labels actor-visible: false
mitigation reference rows ordinary denominator allowed: false
```

Allowed actor inputs remain ego kinematics, IMU-like response, actuator state,
previous physical commands, ego-frame road/free-space/obstacle geometry, and
recurrent command-response state. Forbidden actor inputs include hidden
dynamics parameters, slip, tire force, TTC, reference trajectory, path error,
heading error, controller mode, success/progress labels, oracle feasibility,
and any evaluator label that tells the policy which strategy should be used.

## M2791 Training Objective

M2791 should start from the M2782 candidate checkpoint and use the M2655 source
checkpoint as a reference baseline. The objective is a guarded update, not a
promotion attempt:

```text
base checkpoint:
  runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt

source reference checkpoint:
  runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt

candidate output checkpoint:
  runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/checkpoints/m2791_guardrailed_multi_objective_candidate.pt

training profile:
  short guarded RL or actor-head continuation only
  CPU-compatible default
  bounded update count
  no active config overwrite
  no source checkpoint overwrite
  no base candidate checkpoint overwrite
  no checkpoint promotion
  no validation verdict
```

The primary guard is obstacle-clearance non-regression. Road-margin, yaw-rate,
final-speed, and throttle/brake conflict are separate metrics with separate
gates. M2791 must not collapse them into one scalar score that hides
obstacle-clearance regressions.

## Objective Priority

The M2791 objective should use this priority order:

```text
hard guard 1:
  preserve actor contract and finite observation/action traces

hard guard 2:
  keep mitigation reference rows outside ordinary denominators

hard guard 3:
  obstacle-clearance regression guard

secondary objective:
  retain or improve road-margin directional signal without violating hard guards

secondary objective:
  retain or reduce max absolute yaw-rate without violating hard guards

bounded auxiliary objective:
  avoid final-speed collapse and preserve throttle/brake conflict at zero

diagnostic-only signal:
  mean action delta L1 may be logged but cannot drive promotion
```

Obstacle clearance is a guard, not a reward footnote. If a future M2791
candidate improves road margin while increasing obstacle-clearance regression
rows, the branch must fail closed or route to audit as a negative diagnostic.

## Guard Thresholds

M2791 should predeclare guard thresholds relative to M2787 source-vs-candidate
diagnostic accounting:

```text
obstacle-clearance negative-row guard:
  future candidate must not increase the M2787 obstacle-clearance negative-row
  count on the comparable fresh-holdout surface

obstacle-clearance worst-regression guard:
  future candidate must not worsen the M2787 minimum delta lower tail without
  explicit audit routing

road-margin retention guard:
  road-margin directional signal may be kept only if obstacle-clearance guards pass

yaw-rate retention guard:
  yaw-rate directional signal may be kept only if obstacle-clearance guards pass

throttle/brake conflict guard:
  conflict proxy must remain zero on all audited ordinary rows

promotion guard:
  checkpoint promotion remains false in M2791 regardless of metric direction
```

The exact numerical thresholds may be materialized by the M2791 implementation
from M2787 rows, but the acceptance policy is already fixed here: no
road-margin-only or yaw-rate-only acceptance is allowed.

## Seed Budget

M2791 must not rely on a single seed or on the already-used M2784/M2787
surfaces. The default budget is:

```text
ordinary role families:
  stable_avoidable
  stable_aes
  drift_required_recovery

dynamics axes:
  fresh_nominal_or_role_default
  fresh_fault_delay_noise

stress families:
  recurrent_hidden_reset_stress
  previous_command_history_stress
  held_actuator_history_stress

ordinary training buckets: 18
training seeds per bucket: 3
proof holdout seeds per bucket: 2
behavior-retention seed count: 4
fresh evaluation seed indices: start at 8 or later when feasible
mitigation reference seeds: context-only guard rows
```

M2791 may use role, dynamics, and stress labels to construct evaluator-side
curriculum rows. Those labels must never enter actor observation.

## Gate Separation

M2791 must write separate rows for each gate family:

```text
proof gates:
  actor observation 72/action 3
  no hidden/oracle actor input
  no actor-visible labels
  finite observation and action traces
  source/base/candidate checkpoint lineage and hashes
  mitigation reference rows excluded from ordinary denominators

generalization gates:
  proof holdout seeds separate from training seeds
  future fresh evaluation seeds outside M2784 seed_index 0..3 and M2787 seed_index 4..7 when feasible
  all ordinary role families covered
  both dynamics axes covered
  all belief-stress families covered

behavior-retention gates:
  obstacle-clearance negative-row guard
  obstacle-clearance lower-tail guard
  road-margin retention checked only after obstacle-clearance guard
  yaw-rate retention checked only after obstacle-clearance guard
  throttle/brake conflict zero guard
  mitigation reference guard rows remain outside ordinary denominators

promotion gates:
  checkpoint promotion false
  no winner selected
  no success-rate verdict
  no validation readiness or result
  promotion requires a later manifest after proof, generalization, and behavior-retention audit
```

## Stop And Rollback Criteria

M2791 must stop and mark failure if any of these occur:

```text
observation shape is not 72
action shape is not 3
actor-visible role/dynamics/stress/curriculum/outcome labels appear
hidden or oracle actor features are required
mitigation reference rows enter ordinary denominators
training/proof seed split is incomplete
finite action checks fail
checkpoint lineage cannot be written
candidate checkpoint cannot be hashed
obstacle-clearance regression guard cannot be computed
road-margin/yaw-rate improvements are present but obstacle-clearance guard fails
promotion would be required to interpret the result
```

Rollback criteria:

```text
do not overwrite active config
do not overwrite source checkpoint
do not overwrite M2782 base candidate checkpoint
do not promote M2791 candidate checkpoint
write M2791 candidate only under the M2791 output directory
route to M2792 audit before any interpretation
```

## Failure Taxonomy

M2791 should classify failures with the process-v2 taxonomy:

```text
contract_violation:
  actor input/action contract break, hidden/oracle input, or actor-visible label leak

lineage_invalid:
  missing M2789/M2788/M2787/M2782 artifacts or missing checkpoint hash

metric_artifact:
  single scalar score hides obstacle-clearance regression or tiny action deltas

scenario_sampling_failure:
  incomplete seed split, missing role family, missing dynamics axis, or reused-only holdout surface

behavior_regression:
  obstacle-clearance guard fails, throttle/brake conflict appears, or mitigation guard regresses

objective_overfit:
  road-margin-only tuning, public fresh-holdout overfit, or winner selection

proof_washout:
  mitigation rows used as ordinary successes or guard failures hidden by aggregates
```

## Follow-Up Decision

M2790 admits:

```text
m2791-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-preflight
```

M2791 should be a bounded training/update preflight. It may write a candidate
checkpoint and diagnostic proof/generalization/behavior-retention artifacts for
audit. It must not rank, promote, validate, claim performance, claim paper
evidence, claim current-sim or high-fidelity validation, complete the full
ideal driver gate, or claim level3 self-identification.

The follow-up is only admitted because it changes the evidence axis from
source-only paired delta interpretation to a guardrailed multi-objective update
recipe with explicit behavior-retention gates.
