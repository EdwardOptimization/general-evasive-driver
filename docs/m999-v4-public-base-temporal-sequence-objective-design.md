# M999 V4 Public Base Temporal Sequence Objective Design

## Purpose

M999 designs the first exact objective over the M997 temporal sequence corpus.

This milestone does not train, optimize, run PPO, promote a checkpoint, or
change actor inputs.

## Objective Boundary

The M997 corpus supports this claim:

```text
normal uninterrupted history scores and executes the normal safe sequence
better than temporally disrupted history on source-diverse capability-step rows.
```

It does not support this claim:

```text
cross-fault wrong-history self-identification is proven.
```

Therefore M999 designs a temporal objective, not a cross-fault objective.

## Corpus Inputs

Primary corpus:

```text
runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz
```

Required arrays:

```text
normal_rollout_observations
normal_rollout_actions
normal_initial_hidden
variant_initial_hidden
sequence_mask
row_weight
terminal_margin_gap
variant_id
history_length
```

Metadata:

```text
runs/m997_v4_public_base_temporal_sequence_corpus_export/metadata.csv
```

Only these variants are positive temporal evidence:

```text
reset_then_warm_history
delayed_capability_history
```

Cross-fault/action-response mismatch rows remain diagnostic-only.

## Training Target Principle

Do train toward:

```text
normal uninterrupted history -> normal safe action sequence
```

Do not train toward:

```text
disrupted temporal history -> degraded variant action sequence
```

The variant history exists to test whether the normal history matters. It is
not a desired behavior target.

## Exact Objective Terms

Let:

```text
o_t      = normal rollout observation at step t
a_t      = normal rollout action at step t
h_n      = normal uninterrupted hidden state at the decision point
h_v      = disrupted temporal hidden state at the decision point
w_i      = M997 row_weight
mask_t   = valid sequence mask
```

### 1. Normal Sequence Retention

Keep the policy likely under the normal uninterrupted history:

```text
logp_n = sum_t mask_t * log pi(a_t | o_t, h_n)
L_normal_nll = mean_i w_i * (-logp_n_i / length_i)
```

This is the only direct behavior-imitation target.

### 2. Temporal Preference Separation

Make the normal hidden state score the normal safe sequence better than the
disrupted temporal hidden state:

```text
logp_v_on_n = sum_t mask_t * log pi(a_t | o_t, h_v)

L_temporal_pref =
  mean_i w_i * softplus((logp_v_on_n_i - logp_n_i) / length_i + margin)
```

Initial margin:

```text
margin = 0.05
```

This term uses the variant history only as a contrastive condition. It does not
ask the variant branch to imitate the degraded action sequence.

### 3. Base-KL / Parameter Trust Region

Any future actor update should include an anchor to the M974 public base:

```text
L_base_logp_anchor =
  mean_i w_i * square((logp_n_i - logp_n_base_i) / length_i)
```

This avoids turning a corpus objective into an unconstrained BC pass.

Do not rely on parameter L2 alone. The meaningful trust region is behavioral:

```text
normal action sequence likelihood
public replay gates
behavior seeds
```

### 4. Optional Temporal Gap Floor

M1000 should report but not optimize this initially:

```text
gap = (logp_n - logp_v_on_n) / length
```

The first actor-update milestone may add a hinge only if the no-update evaluator
shows that normal NLL can improve while the temporal gap collapses:

```text
L_gap_floor = mean_i w_i * relu(gap_floor - gap)
```

Initial gap floor should be conservative:

```text
gap_floor = min(base_gap_p10, 0.0)
```

The goal is retention, not making hidden states different for its own sake.

## Combined Objective For Future Actor Update

Initial exact objective:

```text
L = L_normal_nll
  + lambda_pref * L_temporal_pref
  + lambda_anchor * L_base_logp_anchor
```

Initial coefficients for the first design only:

```text
lambda_pref = 1.0
lambda_anchor = 0.25
```

These coefficients are not approved for training yet. M1000 must implement the
exact evaluator first and establish baseline values from the M974 public base.

## Exact Evaluator Requirements

M1000 should implement a no-update evaluator over the M997 corpus.

Required outputs:

```text
row_count
positive_row_count
normal_sequence_nll_mean
temporal_preference_loss_mean
temporal_logp_gap_mean
temporal_logp_gap_p10
temporal_logp_gap_p50
temporal_logp_gap_p90
weighted_normal_sequence_nll
weighted_temporal_preference_loss
weighted_logp_gap_mean
normal_action_replay_l2_max
actor_parameters_changed
training_started
ppo_used
promoted
```

Evaluator checks:

```text
all losses finite
row_weight mean is 1.0
all masks have at least one valid step
normal action replay L2 max <= 1e-5
actor checksum unchanged
```

M1000 should reproduce M997's no-update scale closely enough to catch schema
or loss normalization mistakes.

## Future Actor Update Guard

The first objective-only update after M1000 should be tiny and exact-gated.

Before any candidate can proceed to public replay:

```text
weighted_normal_sequence_nll <= base
weighted_temporal_preference_loss <= base
weighted_logp_gap_mean >= base - tolerance
normal_action_replay_l2_max on corpus <= tolerance
actor input contract unchanged
no training on diagnostic cross-fault rows
```

Then run public replay/proof gates:

```text
M267/M264
M183/M170
six public replay surfaces used by recent promotion gates
behavior seeds 9505 / 9506
reset/zero-all ordering diagnostics
M994/M997 temporal sequence intervention sanity
```

No promotion is allowed from the first objective-only update. It can only become
a candidate for a later full public gate.

## Trainable Surface Guidance

The first actor update should start conservatively:

```text
actor_mean only
```

If actor_mean-only cannot improve exact objective metrics without collapsing
the temporal gap, the next design may consider:

```text
actor_mean + response_context_fusion.0
```

Do not update GRU, response encoder, context encoder, critic, or log_std in the
first temporal objective probe.

## Blocked Routes

Do not:

```text
run PPO;
promote;
train from diagnostic cross-fault rows;
train the disrupted temporal branch toward degraded actions;
ignore row_weight;
claim cross-fault self-ID;
use private holdout;
change actor inputs.
```

## Decision

```text
temporal_sequence_objective_design_admit_exact_evaluator
```

Next:

```text
m1000-v4-public-base-temporal-sequence-objective-evaluator
```
