# M1402 Paper-Route Warmup Reveal Pressure Outcome Result Audit

## Summary

M1402 audits the M1401 margin-banded late-reveal outcome probe.

Decision:

```text
late_reveal_outcome_audit_pivot_to_mild_warmup_stimulus_design
```

M1402 does not train, run PPO, run a new source sweep, promote, use private
holdout, change actor inputs, or export a training corpus.

## M1401 Evidence

M1401 result:

```text
result_class: warmup_latched_outcome_action_only
selected_candidate_rows: 256
outcome_rows: 2048
normal_margin_candidate_rows: 256
broad_near_boundary_candidate_rows: 16
preferred_near_boundary_candidate_rows: 0
accepted_outcome_rows: 0
warmup_history_positive_rows: 0
action_critical_rows: 1464
normal_failed_rows: 16
```

Normal-margin bands:

```text
negative: 2 candidates
broad_0p25_0p50: 16 candidates
high_gt_0p50: 238 candidates
preferred_0p02_0p25: 0 candidates
```

Variant summary:

```text
all variants: 0 outcome-critical rows
reset_hidden sequence_action_l2_mean: 0.9791
warmup_removed sequence_action_l2_mean: 0.6298
warmup_shortened_8 sequence_action_l2_mean: 0.3336
zero_current_response sequence_action_l2_mean: 0.2278
```

## Classification

M1401 is an action-only result:

```text
history/intervention changes actions: yes
history/intervention changes outcome margin: no
preferred near-boundary normal candidates: no
source-diverse accepted outcome rows: no
training admission: blocked
corpus export admission: blocked
```

The key failure mode is not that the actor is insensitive. It is that the task
does not convert action differences into outcome differences.

## Why Not Another Late-Reveal Grid

M1400 already showed:

```text
step 64: 144 matched/bucketed rows
step 72: 80 matched/bucketed rows
step 80: 32 matched/bucketed rows
step 88: 0 matched/bucketed rows
step 96: 0 matched/bucketed rows
```

M1401 then showed:

```text
preferred near-boundary rows: 0
accepted outcome rows: 0
```

This means simply shifting reveal later is nearly exhausted:

```text
64/72/80: reconstructable but too easy or outcome-insensitive
88/96: too late or too sparse for matched/bucketed source rows
```

Another late-reveal sweep would likely overfit public source rows without adding
a new evidence axis.

## Next Route

Open a design milestone for mild warmup stimulus and near-boundary task design.

The next branch step should change the task generator, not the actor input:

```text
1. Mild warmup stimulus:
   use low-risk road/corridor geometry, mild curvature, lane offset, or decel
   cues before emergency reveal so the recurrent state receives useful
   command-response evidence.

2. Near-boundary reveal:
   create scenarios where normal rollouts are viable but closer to the preferred
   0.02-0.25m clearance margin window.

3. Current/recent controls:
   preserve strict or bucketed current matching, zero-current positive control,
   reset-hidden control, wrong-warmup history, delayed-warmup history, and
   shortened/removed warmup.

4. Implementation guard:
   first design the task route and thresholds; then run a source smoke; only
   after source viability should outcome probes run.
```

Next milestone:

```text
m1403-paper-route-mild-warmup-stimulus-design
```

## Guardrails

```text
training_started: false
evaluation_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```
