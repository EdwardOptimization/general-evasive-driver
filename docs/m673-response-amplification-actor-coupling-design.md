# M673 Response-Amplification Actor-Coupling Design

## Purpose

M673 designs the first conservative actor-coupling probe after the positive M671
shadow result and the M672 audit.

This milestone is design-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

The design goal is to turn M671's frozen shadow evidence into a deployable
candidate path without changing the P0 human-view actor input contract.

## Starting Evidence

M671 showed:

```text
shadow_corpus_rows:       648
source_count:             216
physical_pair_count:      100
source_weight_balanced:   true
shadow_passed:            true
passed_view:              fused_plus_next_hidden
view_pass_count:          2/3 seeds
actor_checksum_changed:   false
actor_checkpoint_written: false
ppo_used:                 false
```

M672 classified this as:

```text
shadow_positive_representation_action_boundary_evidence
closed_loop_proof_absent
```

Therefore the next admissible step is not PPO or promotion. It is a small
exact-gated actor-coupling probe.

## Coupling Form

The first coupling should be a frozen-backbone residual sequence head:

```text
base_actor = frozen BC5660 actor
feature_view = concat(fused_feature, next_recurrent_hidden)
delta_sequence = residual_head(feature_view)
candidate_action_t = clip(base_action_t + alpha * delta_sequence[0])
```

Only the first residual is executed in closed loop. The full predicted sequence
is used for exact diagnostics, matching the receding-horizon idea:

```text
predict K-step action residual sequence;
execute only the first action;
re-observe and re-plan at the next step.
```

This does not add any deployable observation input. It uses the same observation
and recurrent hidden state already present in the P0 human-view actor.

## Frozen Versus Trainable Parameters

M674 should start with:

```text
frozen:
  BC5660 actor parameters

trainable:
  residual sequence head only
```

This is intentionally more conservative than mutating the actor backbone. It
tests whether M671's positive fused-plus-next-hidden signal can produce an
action-changing deployable wrapper while keeping the base driver intact.

Backbone fine-tuning remains blocked until a residual-head candidate passes
exact metrics and replay diagnostics.

## Training Targets

Use the M671 shadow corpus:

```text
runs/m671_response_amplification_shadow/shadow_corpus.npz
runs/m671_response_amplification_shadow/shadow_metadata.csv
```

Targets:

```text
normal hidden:
  residual_sequence -> 0

wrong hidden:
  residual_sequence -> target_delta_wrong
```

Loss:

```text
L =
  L_normal_zero
  + lambda_wrong * L_wrong_target
  + lambda_gap * L_gap_margin
  + lambda_smooth * L_sequence_smoothness
```

Initial coefficients:

```text
lambda_wrong: 1.0
lambda_gap:   0.25
lambda_smooth: 0.05
```

The normal branch is a hard gate, not just another average loss.

## Exact Metrics

M674 must report exact metrics before any replay:

```text
normal_delta_l2_mean
normal_delta_l2_p95
predicted_normal_wrong_gap_l2_mean
predicted_normal_wrong_gap_l2_p10
gap_improvement_ratio
wrong_target_mse_improvement
first_residual_l2_mean
first_residual_l2_p95
source-heldout versions of all metrics
```

For execution safety it must also report alpha-scaled first-action drift:

```text
normal_action_drift_first_l2_mean
normal_action_drift_first_l2_p95
wrong_action_drift_first_l2_mean
wrong_action_drift_first_l2_p95
```

## Alpha Ladder

Do not accept the raw residual head directly. Evaluate an interpolation ladder:

```text
alpha: 0.02, 0.05, 0.10, 0.20, 0.50, 1.00
```

For each alpha:

```text
candidate_action = clip(base_action + alpha * residual_first_action)
```

Exact metrics should be computed for both raw residuals and alpha-scaled
executed residuals. The selected candidate is the largest alpha that satisfies
normal-retention and exact gap criteria. If no alpha satisfies the gates, M674
fails as an exact actor-coupling probe and no replay should run.

## Initial Pass Criteria

M674 exact candidate passes only if source-heldout metrics satisfy:

```text
normal_delta_l2_mean <= 0.0025
normal_delta_l2_p95 <= 0.0060
predicted_normal_wrong_gap_l2_mean >= 0.010
predicted_normal_wrong_gap_l2_p10 >= 0.004
gap_improvement_ratio >= 3.0
wrong_target_mse_improvement >= 0.50
normal_action_drift_first_l2_p95 <= 0.0060 at selected alpha
actor_checksum unchanged
no base actor checkpoint written
```

These are exact objective gates, not promotion gates.

## Replay Admission

Closed-loop replay remains a second stage. It may run only after the exact gate
passes.

Initial replay diagnostics should be limited to:

```text
M667 normal-success boundary source rows
M586/M636 matched-current diagnostics if compatible
behavior sentinel seeds
```

Replay failure should be classified specifically:

```text
normal_retention_failure
wrong_history_gap_not_closed_loop_relevant
behavior_regression
metric_artifact
```

No replay result from M674 may promote a driver checkpoint. Promotion requires a
later promotion manifest with proof, generalization, behavior, and holdout
discipline.

## Required Implementation Artifacts

M674 should write:

```text
runs/m674_response_amplification_actor_coupling/summary.json
runs/m674_response_amplification_actor_coupling/alpha_summary.csv
runs/m674_response_amplification_actor_coupling/seed_view_summary.csv
runs/m674_response_amplification_actor_coupling/residual_head_*.pt
docs/m674-response-amplification-actor-coupling-implementation.md
```

The residual head checkpoints are allowed. A base actor checkpoint is not.

## Rejected Shortcuts

Do not:

- train with PPO;
- mutate the BC5660 actor backbone;
- change actor observations;
- introduce labels or hidden parameters into actor input;
- tune on private holdout;
- promote from this probe;
- claim closed-loop self-identification before replay evidence exists.

## Decision

```text
response_amplification_actor_coupling_design_admit_m674
```

## Next

```text
m674-response-amplification-actor-coupling-implementation
```
