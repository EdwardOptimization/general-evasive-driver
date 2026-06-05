# M2781 Engineering Controller Route A Source-Only Belief-Stress Short-Training Continuation Design

## Metadata

- status: completed
- decision: `admit_source_only_belief_stress_short_training_continuation_preflight`
- manifest: `experiments/manifests/m2781-engineering-controller-route-a-source-only-belief-stress-short-training-continuation-design.json`
- design doc: `docs/m2781-engineering-controller-route-a-source-only-belief-stress-short-training-continuation-design.md`
- parent audit: `docs/m2780-engineering-controller-route-a-source-only-belief-stress-training-admission-pack-materialization-result-audit.md`
- parent summary: `runs/m2779_engineering_controller_route_a_source_only_belief_stress_training_admission_pack_materialization/summary.json`
- source checkpoint: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt`
- follow-up manifest: `experiments/manifests/m2782-engineering-controller-route-a-source-only-belief-stress-short-training-continuation-preflight.json`
- next: `m2782-engineering-controller-route-a-source-only-belief-stress-short-training-continuation-preflight`

## Design Scope

M2781 is design-only. It admits a bounded M2782 short-training continuation
preflight, but M2781 itself does not execute reset, step, policy action,
rollout, replay, validation, training, PPO, source build, adapter probe,
external simulation, ranking, winner selection, checkpoint promotion,
success-rate verdict computation, driver-performance measurement, paper
evaluation, high-fidelity validation, full-driver gate, or self-ID proof.

The design converts M2779 source-only admission metadata into a future
fresh-evidence branch. It does not treat M2779 rows as training success,
validation result, ranking metric, or self-ID evidence.

## Parent Evidence

M2780 accepted M2779 as complete and claim-safe:

```text
M2779 status_pass: true
M2779 gate_matrix_pass: true
admission rows: 96
curriculum rows: 24
mitigation guard rows: 8
actor guard rows: 7
claim rows: 19
gate rows: 39
```

M2779 preserves the source-only diagnostic accounting:

```text
M2773 candidate rows: 32
M2773 execution rows: 128
M2773 trace rows: 10240
M2773 collision diagnostic rows: 32
M2773 road-departure diagnostic rows: 68
M2775 delta rows: 96
M2775 matched trace pair rows: 7680
M2775 road-departure removed rows: 4
M2775 road-departure added rows: 0
M2775 collision changed rows: 0
```

M2779 admission signals:

```text
behavior-outcome-sensitive rows: 4
action-response-sensitive rows: 53
trace-sensitive rows: 15
weak/context rows: 24
ordinary admission rows: 72
mitigation/context rows: 24
```

These rows are source-only diagnostic admission metadata. They can define a
future training curriculum proposal, but they cannot become actor-visible
labels, ordinary success denominators, ranking criteria, or performance proof.

## Actor Contract

M2782 must preserve the deployed actor contract:

```text
observation shape: 72
action shape: 3
action mapping: steer, throttle, brake
hidden/oracle actor input allowed: false
actor input feature addition allowed: false
stress/admission/curriculum labels actor-visible: false
role/dynamics/intervention labels actor-visible: false
outcome/progress/success/verdict labels actor-visible: false
mitigation reference rows ordinary denominator allowed: false
```

Allowed actor inputs remain ego kinematics, IMU-like response, actuator state,
previous physical commands, ego-frame road/free-space/obstacle geometry, and
recurrent command-response state. Forbidden actor inputs include hidden
dynamics parameters, slip, tire force, TTC, reference trajectory, path error,
heading error, controller mode, success/progress labels, oracle feasibility,
and any admission or curriculum labels.

## M2782 Training Objective

M2782 should run a bounded short-training continuation only if it can preserve
the actor contract and write full evidence artifacts. The training objective is
not to optimize a public gate. It is to test whether the M2655 source-only
driver can be nudged toward better command-response robustness under the
M2779 belief-stress curriculum while preserving mitigation and behavior
guards.

The proposed M2782 update is deliberately small:

```text
source checkpoint:
  runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt

candidate checkpoint:
  runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt

training profile:
  short guarded RL or actor-head continuation only
  CPU-compatible default
  bounded update count
  no active config overwrite
  no checkpoint promotion
  no validation verdict
```

M2782 may use M2779 curriculum rows to choose scenario roles, dynamics axes, and
stress families for training proposals. The actor must never receive those
labels as observations. The training code may log them as evaluator metadata
only.

## Seed Budget

M2782 must not rely on a single seed. The default seed budget is:

```text
ordinary role families: stable_avoidable, stable_aes, drift_required_recovery
dynamics axes: fresh_nominal_or_role_default, fresh_fault_delay_noise
stress families: recurrent_hidden_reset_stress, previous_command_history_stress, held_actuator_history_stress
training seeds per role/axis bucket: 3
proof holdout seeds per role/axis bucket: 1
mitigation reference seeds: context-only, guard/proof rows only
minimum ordinary training buckets: 18
minimum ordinary proof buckets: 18
```

If the implementation cannot create the full training/proof split, M2782 must
stop and route to artifact repair or synthesis. It must not silently shrink to
one seed or one public proof row.

## Curriculum Mapping

M2782 should map M2779 buckets as follows:

```text
high_audit_required:
  include in proof-first rows and training proposals, but never rank as winner

medium_audit_required:
  include in training proposals and proof rows

low_audit_required:
  include as trace-sensitivity coverage, not as success evidence

context_only:
  mitigation/reference guard only; never ordinary training success
```

The curriculum mapping is actor-invisible. The model should learn from
closed-loop reward and command-response experience, not from labels that tell
it which role, dynamics axis, stress family, outcome, or admission class it is
in.

## Gate Separation

M2782 must separate gates:

```text
proof gates:
  actor contract 72/3
  no hidden/oracle actor input
  no actor-visible labels
  stress-family coverage present
  mitigation reference rows excluded from ordinary denominators
  no regression on protected mitigation rows
  finite action and observation traces

generalization gates:
  held-out seed rows are separate from training rows
  both nominal and fault-delay-noise dynamics axes are covered
  stable_avoidable, stable_aes, and drift_required_recovery roles are covered
  no single-seed verdict

promotion gates:
  checkpoint promotion is false in M2782
  no winner selected
  no success-rate verdict
  promotion requires a later manifest after proof and generalization gates pass
```

M2782 may write a candidate checkpoint for audit. It must not promote it.

## Stop And Rollback Criteria

M2782 must stop and mark failure if any of these happen:

```text
observation shape != 72
action shape != 3
actor-visible stress/admission/curriculum/outcome labels appear
hidden or oracle actor features are required
mitigation rows enter ordinary denominators
training/proof seed split is incomplete
finite action checks fail
checkpoint lineage cannot be written
candidate checkpoint cannot be hashed
protected mitigation guard regresses beyond the predeclared guard
```

Rollback criteria:

```text
do not overwrite active config
do not overwrite source checkpoint
do not promote candidate checkpoint
write candidate checkpoint only under M2782 output directory
route to M2783 audit before any interpretation
```

## Failure Taxonomy

M2782 should classify failures with the process-v2 taxonomy:

```text
contract_violation:
  actor input/action contract break, hidden/oracle input, or actor-visible label leak

lineage_invalid:
  missing M2779/M2780 source artifacts, missing source checkpoint, or missing checkpoint hash

metric_artifact:
  success-rate verdict, ranking, or admission labels used as proof

scenario_sampling_failure:
  incomplete seed split, missing role family, or missing dynamics axis

behavior_regression:
  protected mitigation or baseline behavior guard regression

objective_overfit:
  fixed public gate optimization, single-seed tuning, or winner selection

proof_washout:
  mitigation rows used as ordinary successes or proof rows hidden by aggregates
```

## Follow-Up Decision

M2781 admits:

```text
m2782-engineering-controller-route-a-source-only-belief-stress-short-training-continuation-preflight
```

M2782 may implement the bounded short-training continuation preflight and write
candidate checkpoint, training rows, proof gate rows, generalization gate rows,
promotion guards, actor guards, mitigation guards, claim rows, gate matrix,
summary, doc, run-state, and one M2783 result-audit manifest. M2782 may run
bounded training only within that manifest. M2782 must not validate, rank,
promote, or claim driver performance.

## Rejected Claims

M2781 does not support:

```text
driver performance
repair success
training result
validation readiness
validation result
current-sim verdict
high-fidelity validation
paper evidence
finite-window-vs-GRU conclusion
level3 self-identification
full ideal driver completion
```
