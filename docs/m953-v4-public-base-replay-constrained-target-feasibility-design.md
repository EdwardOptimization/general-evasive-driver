# M953 V4 Public Base Replay-Constrained Target Feasibility Design

## Purpose

M953 designs the next branch after M952. It is design-only.

It does not train, run PPO, widen actor inputs, open encoders/GRU, run a full
public replay stack, use private holdout, or promote a checkpoint.

The question is narrower and more basic:

```text
Do replay-constrained targets exist inside the current trust region?
```

The controlled-fusion branch showed that parameter-space objectives can move
one side of the proof while breaking another. Before more actor updates, the
project should test whether the desired targets are themselves compatible.

## Diagnosis From M952

M942/M944 found exact-compatible controlled-fusion candidates:

```text
candidate alphas: 0.0675, 0.0700, 0.0725
strict exact candidates: true
forbidden parameters changed: false
```

M946/M947 rejected them under closed-loop replay:

```text
failed surface: M267/M264
success_drop_count: 17 -> 13
failed rows: 6, 13, 15, 16
failure_type: proof_washout
```

M949/M951 added explicit rejected-branch retention. That fixed the M267
preflight over a broad alpha range but did not create an exact-compatible
candidate:

```text
M951 M267 preflight pass alpha count: 13
M951 exact candidate alpha count: 0

alphas <= 0.050:
  normal_retention_pass: true
  M267 preflight: pass
  tail_lift_pass: false

alphas >= 0.0675:
  tail_lift_pass: true
  M267 preflight: pass
  normal_retention_pass: false
```

This means the next bottleneck is not simply wrong-history retention. The
active question is whether the low-tail target movement, normal retention, and
M267 wrong-history proof can be satisfied together at the target level.

## Target Feasibility Definition

M954 should not optimize actor parameters. It should search target actions or
short target action sequences around existing surfaces and ask whether at least
one target family satisfies all three constraints:

```text
1. normal retention
2. low-tail lift
3. M267/M264 wrong-history proof retention
```

The audit is allowed to use reconstructed observations, hidden states, base
actions, existing candidate directions, accepted target rows, and no-training
action/sequence overrides in the simulator. It is not allowed to change the
actor input contract or update model weights.

## Active Sets

Use two active sets.

### Low-Tail Objective Rows

Primary rows:

```text
runs/m951_v4_public_base_rejected_branch_boundary_retune_probe/objective_rows.csv
runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv
runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv
```

The audit should evaluate the same exact metrics used by the controlled-fusion
probes:

```text
normal_anchor_mse_mean
normal_anchor_mse_p95
first_action_drift_from_base_mean
first_action_drift_from_base_p95
normal_intervention_gap_p10
gap_deficit_mean
low_tail_fraction
target_action_mse_mean
strict_target_action_mse_mean
```

### Rejected-History Proof Rows

Primary rows:

```text
M267/M264 rows: 6, 13, 15, 16
```

Use:

```text
runs/m951_v4_public_base_rejected_branch_boundary_retune_probe/active_rejected_branch_rows.csv
runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
```

The proof condition remains closed-loop and branch-specific:

```text
normal-history branch: success
wrong-history branch: failure
success_drop_count: 17 / 17 on M267/M264
active rows 6, 13, 15, 16: pass
```

## Candidate Target Families

M954 should compare several target families without training.

### Family A: Existing Direction Targets

Use materialized or reconstructable directions from:

```text
M940 raw controlled-fusion direction
M949 rejected-branch retention direction
M951 lower-boundary retune direction
M944 alpha candidates
M951 preflight checkpoints
```

This family answers whether any already discovered direction contains a target
point that the previous alpha grids missed.

### Family B: Low-Tail Projection Targets

For each low-tail row, construct the smallest action-space move that would
clear the registered low-tail thresholds while preserving normal-retention
thresholds:

```text
normal_action_target =
  base_normal_action
+ projected_delta_away_from_intervention
```

Clamp the target by row-level trust limits:

```text
normal_action_drift <= 0.003 mean-level budget
normal_anchor_mse <= 0.000004 mean-level budget
action bounds: [-1, 1]
```

This is an offline target feasibility check. It does not claim an actor can fit
the targets until a later implementation tests fit and replay.

### Family C: Branch-Separated Proof Targets

For M267 rows 6, 13, 15, and 16, build separate targets for normal hidden and
wrong hidden:

```text
normal_hidden target:
  stay near the base normal action or the best normal-success override

wrong_hidden target:
  stay near the base wrong-history action or a wrong-failure-preserving override
```

This family encodes the actual self-identification relation:

```text
same current scene;
different command-response history;
different branch action should remain behaviorally different.
```

The target set should not force wrong-history branches toward the normal safe
action. M279-M286 already showed that this is how proof rows get washed out.

### Family D: Short-Horizon Sequence Targets

If one-step targets are inconclusive, M954 may test short target sequences:

```text
horizon: 2 or 4 control steps
execute: override only inside no-training feasibility replay
```

The deployed actor output contract remains single-step `[steer, throttle,
brake]`. Sequence targets are only a diagnostic for whether first-action targets
are under-specified.

## Feasibility Gates

The implementation should evaluate gates in this order.

### Gate 1: Contract Gate

Required:

```text
actor inputs unchanged
no hidden parameters used by deployable actor
no training
no PPO
no checkpoint promotion
private holdout not used
```

Training-time target construction may read simulator labels or outcome rows,
but only to build diagnostics and offline target corpora. Those values must not
be added to actor observations.

### Gate 2: Offline Exact Target Gate

Substitute candidate target actions into the exact low-tail evaluator and
require:

```text
normal_retention_pass: true
tail_lift_pass: true
target_tolerance_pass: true
```

Report:

```text
exact_target_family_count
exact_target_candidate_count
best_normal_retained_tail_lift_candidate
best_normal_safe_low_tail_trend_candidate
row_conflict_count
```

### Gate 3: M267 Active-Row Closed-Loop Target Gate

Using no-training branch-specific action or short-sequence overrides, require:

```text
rows 6, 13, 15, 16:
  normal branch succeeds
  wrong-history branch fails

full M267/M264:
  success_drop_count == 17
  normal_success_delta >= 0.0
  normal_margin_mean_delta >= -0.005
  margin_gap_mean_delta >= -0.001
```

This is still a preflight, not full promotion evidence.

### Gate 4: Joint Feasibility Gate

Accept a target family only if the same target construction passes both:

```text
offline exact target gate
M267 active-row closed-loop target gate
```

If the gates are passed by different target families, the result is not a
feasible joint target. It is a conflict that must be documented.

## Required Artifacts For M954

M954 should write:

```text
runs/m954_v4_public_base_replay_constrained_target_feasibility/summary.json
runs/m954_v4_public_base_replay_constrained_target_feasibility/target_family_summary.csv
runs/m954_v4_public_base_replay_constrained_target_feasibility/offline_exact_target_metrics.csv
runs/m954_v4_public_base_replay_constrained_target_feasibility/m267_target_preflight.csv
runs/m954_v4_public_base_replay_constrained_target_feasibility/row_conflicts.csv
```

The summary must include:

```text
training_started: false
ppo_used: false
promoted: false
actor_input_contract_changed: false
exact_target_candidate_count
m267_target_preflight_pass_count
joint_feasible_target_count
result_class
next_blocker
```

## Route Logic

If `joint_feasible_target_count > 0`:

```text
route: target export and actor-fit objective design
```

The next milestone should export the compact target corpus and design a
parameter update that tries to fit those targets under the same public gates.

If exact target candidates exist but M267 target preflight fails:

```text
route: rejected-history target refinement or branch-separated sequence targets
```

This means low-tail targets are possible but still repair the wrong-history
branch into safety.

If M267 target preflight passes but exact low-tail target gate fails:

```text
route: low-tail threshold audit or wider action/sequence target audit
```

This means proof-preserving targets exist, but they do not move the low-tail
objective enough under the registered thresholds.

If no target family can pass either side:

```text
route: synthesis before widening actor surface
```

Do not open encoders/GRU merely because this audit fails. First classify
whether the failure is an action-space infeasibility, a threshold artifact, or
a missing target-family problem.

## Decision For Next Milestone

M953 routes to:

```text
m954-v4-public-base-replay-constrained-target-feasibility-implementation
```

M954 should implement the no-training feasibility audit described above. It
must not train, run PPO, or promote.
