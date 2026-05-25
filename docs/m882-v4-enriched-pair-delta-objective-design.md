# M882 V4 Enriched Pair-Delta Objective Design

## Purpose

M882 designs the objective loss and implementation prerequisites for the M880
enriched pair-delta corpus.

The design question is:

```text
Given rows with normal_action, paired/right_action, and first_override_action,
what exact objective-sanity loss should be implemented before any actor update?
```

M882 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## Inputs

Primary corpus:

```text
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_train_public_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_eval_public_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_source_holdout_public_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_new_signature_holdout_public_rows.csv
```

Each row has:

```text
normal_action:
  normal_first_steer / throttle / brake

right_action:
  right_first_steer / throttle / brake

override_action:
  first_override_steer / throttle / brake

outcome labels:
  accepted_class
  margin_delta
  abs_margin_delta
  terminal_reason
  sequence_margin
```

## Required Tensor Reconstruction

The enriched CSV rows are not enough to compute a policy objective by
themselves. M883 must recover or regenerate an exact tensor corpus containing:

```text
observation frame at the target step
normal/correct recurrent hidden state
paired/right recurrent hidden state when used
normal_action
right_action
override_action
accepted_class
margin_delta
split
row weight
row identity and dedup metadata
```

If these tensors cannot be reconstructed deterministically, M883 must stop and
route to a tensor-corpus regeneration branch. It must not approximate missing
hidden state with reset hidden unless the row is explicitly labeled as such.

## Objective Terms

M883 should first implement an exact no-update sanity evaluator. The evaluator
computes log probabilities under the current policy for the same observation
and hidden state:

```text
logp_normal   = log pi(normal_action   | observation, normal_hidden)
logp_override = log pi(override_action | observation, normal_hidden)
```

For `pair_delta_improvement` rows, the pair-delta override improved margin or
terminal outcome, so the preferred ordering is:

```text
logp_override >= logp_normal + m_improve
```

Loss:

```text
L_improve = w * softplus(logp_normal - logp_override + m_improve)
```

For `pair_delta_degradation` rows, the override harmed margin or terminal
outcome, so the preferred ordering is:

```text
logp_normal >= logp_override + m_reject
```

Loss:

```text
L_reject = w * softplus(logp_override - logp_normal + m_reject)
```

Suggested initial margins:

```text
m_improve = 0.05
m_reject = 0.05
```

These are exact objective-sanity metrics, not yet a training recipe.

## Optional Paired-Hidden Diagnostic

M883 may also compute a paired-hidden diagnostic:

```text
logp_right_action_under_right_hidden
logp_right_action_under_normal_hidden
logp_override_under_right_hidden
```

But this must remain diagnostic unless the tensor reconstruction can guarantee
that the paired/right hidden state is aligned with the row identity.

## Weights

M883 should use deterministic capped row weights:

```text
base_weight = objective_sample_weight
outcome_weight = clip(abs_margin_delta / 0.01, 1.0, 5.0)
collision_bonus = 2.0 if terminal_reason == collision else 1.0
weight = clip(base_weight * outcome_weight * collision_bonus, 1.0, 10.0)
```

The evaluator must report weighted and unweighted losses. Later update recipes
may adjust weights, but M883 should not tune them to pass a downstream gate.

## Split Discipline

M883 must report metrics separately for:

```text
objective_train_public
objective_eval_public
source_holdout_public
new_signature_holdout_public
```

Use policy:

```text
train split:
  exact sanity and future fitting candidate

eval split:
  public diagnostic, not for fitting the same objective coefficients

source_holdout split:
  existing-evidence source diagnostic only; contains no new M873 rows

new_signature_holdout split:
  public within-source duplicate/behavior overfit diagnostic
```

Do not claim source-held-out new-evidence generalization because:

```text
source_holdout_new_rows_enriched: 0
```

## Exact Sanity Gates

M883 should pass only if:

```text
tensor_rows_reconstructed > 0
train_rows_reconstructed == 124
eval_rows_reconstructed == 22
source_holdout_rows_reconstructed == 98
new_signature_holdout_rows_reconstructed == 3
missing_tensor_count == 0
exact_losses_finite == true
improvement_rows_present == true
degradation_rows_present == true
per_split_metrics_written == true
training_started == false
optimizer_started == false
ppo_used == false
promoted == false
```

M883 should not require the current base policy to already prefer the better
action. It should only determine whether the exact objective can be computed
and whether its signal is nondegenerate.

## Failure Taxonomy

`metric_artifact`:

```text
if action targets are evaluated without the correct observation/hidden state.
```

`objective_overfit`:

```text
if only train split metrics are reported or coefficients are tuned against
new-signature holdout.
```

`scenario_sampling_failure`:

```text
still applies because new source holdout is unavailable and 78055 remains a
caveat.
```

`contract_violation`:

```text
if actor observations include hidden parameters, planner labels, TTC, path
errors, or any forbidden shortcut.
```

`lineage_invalid`:

```text
if the tensor reconstruction cannot prove that observation, hidden state, and
action targets come from the same row identity.
```

## Decision

Decision:

```text
enriched_pair_delta_objective_design_admit_m883
```

Next:

```text
m883-v4-enriched-pair-delta-objective-sanity-implementation
```

M883 may implement exact no-update objective sanity. Actor update, residual-head
update, PPO, and checkpoint promotion remain blocked.
