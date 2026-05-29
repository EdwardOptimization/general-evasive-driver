# M1406 Paper-Route Mild Warmup Outcome Result Audit

## Summary

M1406 audits the M1405 mild warmup stimulus outcome probe before any new
source change, corpus export, or training.

Decision:

```text
mild_warmup_outcome_audit_pivot_to_pre_emergency_gate_stimulus_design
```

M1406 does not train, run PPO, promote, use private holdout, change actor
inputs, or export a training corpus.

## M1405 Evidence

M1405 result:

```text
result_class: warmup_latched_outcome_reset_or_current_only
selected_candidate_rows: 282
outcome_rows: 2256
broad_near_boundary_candidate_rows: 93
preferred_near_boundary_candidate_rows: 26
accepted_outcome_rows: 2
warmup_history_positive_rows: 0
accepted_reset_rows: 2
accepted_zero_current_rows: 0
action_critical_rows: 1584
normal_failed_rows: 744
```

Normal-margin bands:

```text
negative: 92 candidates
viable_0p00_0p02: 2 candidates
preferred_0p02_0p25: 26 candidates
broad_0p25_0p50: 65 candidates
high_gt_0p50: 97 candidates
```

Variant summary:

```text
reset_hidden: outcome_critical=2
warmup_removed: outcome_critical=0
warmup_shortened_8: outcome_critical=0
zero_current_response: outcome_critical=0
delayed_warmup_history_16: outcome_critical=0
delayed_warmup_history_8: outcome_critical=0
wrong_warmup_history_same_reveal: outcome_critical=0
same_recent_wrong_warmup_history: outcome_critical=0
```

## Classification

M1405 is not source-positive self-identification evidence:

```text
near-boundary candidate sparsity: improved
preferred-window candidates: present
action sensitivity: present
accepted outcome rows: reset-only, high-margin, seed-singleton
warmup-history-positive rows: absent
wrong-warmup outcome necessity: absent
delayed-history outcome necessity: absent
training admission: blocked
corpus export admission: blocked
```

The two accepted rows cannot support a self-identification claim because they
are:

```text
variant: reset_hidden
normal_margin_band: high_gt_0p50
success_drop: false
unique_source_seeds: 1
unique_capability_pairs: 1
```

## What M1405 Did Improve

M1405 is still useful as task-design evidence. M1401 had zero preferred-window
candidates; M1405 has:

```text
preferred_near_boundary_candidate_rows: 26
preferred unique_source_seeds: 6
preferred unique_capability_pairs: 9
preferred unique_reveal_buckets: 12
```

That means the figure-eight plus tighter obstacle pressure can place rollouts
near the outcome boundary. The missing piece is not only outcome pressure; it is
fault-specific warmup-history relevance.

## Why Not Train Or Export A Corpus

Training from M1405 would optimize the wrong evidence:

```text
no warmup-history-positive rows
no wrong-warmup positives
no delayed-history positives
accepted rows are reset-only and high-margin
```

Using these rows as a corpus would likely teach generic recurrent/reset
robustness, not driver-like online self-identification.

## Why Not Repeat The Same Figure-Eight Grid

The current passive figure-eight route has already shown its limits:

```text
source materialization: pass
near-boundary candidates: pass
wrong/delayed warmup outcome gaps: fail
```

Repeating the same grid with small radius/width/distance tweaks would mainly
optimize public rows. It would not add a new mechanism for creating
fault-specific command-response evidence.

## Next Route

M1407 should design a stronger non-oracle pre-emergency stimulus.

The route should preserve the actor contract:

```text
allowed:
  visible road/free-space/obstacle geometry
  pre-emergency gate, corridor kink, or mild obstacle sequence
  existing ego response/action history and online GRU
  hidden faults as simulator-side labels only

forbidden:
  scripted controller mode
  direct command injection
  actor oracle labels
  hidden parameter inputs
  path error / reference trajectory inputs
  TTC / required clearance / feasibility labels
```

The preferred design is a pre-emergency gate stimulus:

```text
warmup phase:
  low-risk visible gate/corridor/offset geometry forces natural steering,
  braking, or throttle modulation through the existing policy.

reveal phase:
  emergency obstacle is revealed later with matched or bucketed current state.

interventions:
  wrong warmup history, delayed warmup history, warmup removed, reset hidden,
  zero current response.
```

This should create stronger command-response evidence than passive curvature
without adding actor inputs.

## M1407 Requirements

M1407 should be design only. It should decide whether the implementation uses:

```text
1. existing obstacle slots with a warmup gate plus emergency obstacle;
2. road/free-space boundary shaping only;
3. a small task API extension for multi-stage visible obstacle geometry.
```

M1407 must not run a source smoke until it specifies:

```text
actor-contract guardrails
source reconstruction metrics
near-boundary outcome criteria
wrong/delayed warmup variants
stop conditions
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
