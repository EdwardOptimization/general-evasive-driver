# M1291 Paper-Route Source-History Directional Repair Design

## Summary

M1291 designs the next no-PPO repair path after M1290 classified the M1288
objective update as magnitude compression.

Decision:

```text
source_history_directional_repair_design_admit_actor_mean_feasibility_probe
```

Do not continue blind scalar-loss actor-head updates. Do not start PPO.

The next step should implement a diagnostic actor-mean directional feasibility
probe:

```text
m1292-paper-route-source-history-actor-mean-directional-feasibility-probe
```

## Blocker

M1290 showed:

```text
row_count: 152
loss_improved_count: 152
loss_improved_fraction: 1.0
combined_loss_delta_mean: -11.4311475093
after_mutually_exclusive_count: 152
after_mutually_exclusive_fraction: 1.0
after_both_positive_count: 0
min_abs_margin_decreased_count: 152
```

Interpretation:

```text
M1288 reduced exact loss by shrinking residual magnitude, but every row still
has exactly one side of the desired directional relation correct. It did not
create correct-history and wrong-history preference agreement on the same row.
```

This blocks:

```text
PPO;
promotion;
public replay gate escalation;
longer actor_mean scalar-loss continuation.
```

## Repair Options

### Option A: Continue M1288 Scalar Loss

Reject for the next milestone.

Reason:

```text
The M1288 objective is already connected and trainable, yet M1290 shows it
improves by magnitude compression. More steps or a larger learning rate would
likely keep optimizing the same failure mode.
```

### Option B: Pair-Group Directional Objective

Keep as a later repair candidate.

A pair-group objective would treat the two rows in each
`pair_id/probe_template` group together and optimize the minimum row-wise
directional margin:

```text
min_margin = min(correct_preference_margin, wrong_history_preference_margin)
L_pair = softplus(target_margin - min_margin)
```

But before designing this as an update, check whether the fixed features plus
`actor_mean` can satisfy the directional inequalities at all.

### Option C: Trainable-Scope Escalation

Reserve for after feasibility evidence.

Escalating to:

```text
response_context_fusion + actor_mean
response_encoder + GRU + fusion + actor_mean
```

is plausible if actor_mean-only is capacity-limited. It should not be the next
step because it has a larger blast radius and could alter the history
representation before we know the final linear head is actually insufficient.

### Option D: Corpus Relabel Or Refresh

Reserve for conflict evidence.

If actor_mean feasibility probe finds severe contradiction in paired rows, the
next step should audit whether preferred/rejected actions or branch labels are
inconsistent under the current source-history construction.

## Chosen Next Step

Choose a no-PPO actor-mean directional feasibility probe.

Rationale:

```text
For a Gaussian policy with fixed log_std, the log-probability preference between
two fixed actions is a linear inequality in the actor_mean output. With fixed
features, this becomes a linear feasibility question for the actor_mean head.
```

Therefore M1292 should ask:

```text
Can any bounded actor_mean-only head make both correct-history and wrong-history
preferences positive for a meaningful fraction of the 152 public rows?
```

This is more informative than another scalar-loss update.

## M1292 Probe Design

M1292 should:

```text
load the M1154 public-gate base;
reuse M1280/M1277 source-history artifacts;
compute fixed fused features for correct-history and wrong-history current
observations;
freeze all non-actor_mean parameters;
run deterministic actor_mean-only directional feasibility optimization;
try at least base-init and M1288-init;
write row-wise before/after directional metrics;
write parameter-delta diagnostics;
not promote any checkpoint.
```

Candidate loss:

```text
correct_margin = logp_cp - logp_cr
wrong_margin   = logp_wr - logp_wp
min_margin     = min(correct_margin, wrong_margin)

L_directional =
  mean(softplus(target_margin - correct_margin))
+ mean(softplus(target_margin - wrong_margin))
+ lambda_min * mean(softplus(target_margin - min_margin))
+ lambda_anchor * ||actor_mean - actor_mean_base||^2
```

Suggested defaults:

```text
target_margin: 0.05
lambda_min: 2.0
lambda_anchor: 0.001
steps: 300
learning_rate: 0.0003
initializations: base, m1288
```

M1292 may save diagnostic candidates, but none are promotable.

## M1292 Pass/Fail Gates

Primary directional metrics:

```text
both_directional_fraction
correct_positive_fraction
wrong_history_positive_fraction
after_both_positive_count
after_mutually_exclusive_fraction
min_margin_mean
min_margin_p10
```

A strong actor_mean feasibility signal:

```text
both_directional_fraction >= 0.50
and after_both_positive_count > 0
and after_mutually_exclusive_fraction < 1.0
and non_actor_mean_mutation_detected == false
```

A negative capacity signal:

```text
all attempted initializations keep both_directional_fraction == 0.0
or after_mutually_exclusive_fraction == 1.0
```

If strong:

```text
route to result audit and then old-public proof-retention design.
```

If negative:

```text
route to trainable-scope escalation design or corpus relabel/refresh audit.
```

If mixed:

```text
route to pair-group directional objective design with exact row diagnostics.
```

## Guardrails

M1292 must not:

```text
run PPO;
promote a checkpoint;
use private holdout;
change actor observations;
add source/fault/condition/pair/probe labels to actor input;
update GRU, encoders, fusion, critic, log_std, or sequence-tail parameters;
claim closed-loop driver improvement;
claim paper-level evidence;
claim level3 self-identification.
```

## Claim Discipline

M1291 supports only:

```text
A bounded no-PPO diagnostic path exists for testing whether actor_mean-only can
repair M1290 row-wise directional conflict.
```

M1291 does not support:

```text
directional repair success;
closed-loop source adaptation;
PPO readiness;
promotion;
paper-level generalization;
level3 anticipatory self-identification.
```

PPO and promotion remain blocked.
