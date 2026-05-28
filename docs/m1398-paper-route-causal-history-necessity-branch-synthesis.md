# M1398 Paper-Route Causal History Necessity Branch Synthesis

## Summary

M1398 synthesizes the M1390-M1397 causal history-necessity branch after the
warmup-latched full sweep remained source-narrow.

Synthesis decision:

```text
promote_to_next_branch
```

Decision:

```text
causal_history_necessity_synthesis_promote_to_warmup_reveal_pressure_redesign
```

Closed branch:

```text
paper_route_causal_history_necessity_task_design
```

Opened branch:

```text
paper_route_warmup_reveal_pressure_redesign
```

This synthesis does not train, run PPO, run new evaluation, promote a
checkpoint, use private holdout, change actor inputs, or export a training
corpus.

## Evidence Summary

M1390 designed four causal history-necessity task families:

```text
matched-current older-history ambiguity
warmup-latched capability identification
tail-aligned critical-window wrong history
source-rich temporal sequence diagnostics
```

M1391 materialized matched-current source rows:

```text
candidate_rows: 631
matched_current_pairs: 631
unique_source_seeds: 46
unique_fault_pairs: 9
older_history_l2_p95: 0.02730
current_hidden_l2_p95: 0.10404
```

M1392 found broad outcome sensitivity but not source-diverse self-ID:

```text
accepted_outcome_rows: 633
accepted_self_id_rows: 24
accepted_self_id_unique_seeds: 1
accepted_reset_rows: 363
accepted_zero_current_rows: 246
wrong_same_current_history: 0 accepted rows
same_recent_wrong_older_history: 0 accepted rows
```

M1393 designed a two-phase warmup then emergency reveal task, and M1394 showed
the source route can be materialized:

```text
M1394 source_rows: 2580
M1394 matched_or_bucketed_reveal_rows: 604
M1394 matched/bucketed unique_source_seeds: 27
M1394 matched/bucketed unique_capability_pairs: 16
M1394 matched/bucketed unique_reveal_buckets: 131
```

M1395 probed a capped subset:

```text
selected_candidate_rows: 384
outcome_rows: 3072
warmup_history_positive_rows: 12
accepted_warmup_history_unique_source_seeds: 1
wrong_warmup_history outcome-critical rows: 0
same_recent_wrong_warmup_history outcome-critical rows: 0
delayed_warmup_history outcome-critical rows: 0
```

M1397 swept all M1394 matched/bucketed rows:

```text
selected_candidate_rows: 604
outcome_rows: 4832
warmup_history_positive_rows: 31
accepted_warmup_history_unique_source_seeds: 1
accepted_warmup_history_unique_capability_pairs: 9
accepted_warmup_history_unique_reveal_buckets: 5
wrong_warmup_history outcome-critical rows: 0
same_recent_wrong_warmup_history outcome-critical rows: 0
delayed_warmup_history outcome-critical rows: 0
```

M1397 rules out the simple explanation that M1395 was sparse only because of
the 384-row cap.

## Supported Claims

The following claims are supported:

```text
1. The harness can materialize source-diverse matched-current and warmup-latched
   public rows without actor-input leakage.
2. Reset-hidden and zero-current-response controls expose broad current/history
   sensitivity in existing tasks.
3. Warmup removed/shortened interventions can change clearance margin in a
   repeatable seed-139421 source pocket.
4. The current public base and task harness are suitable for no-training
   diagnosis before corpus export or PPO.
```

These are useful engineering and diagnostic claims. They are not enough for a
paper-level self-identification claim.

## Unsupported Or Falsified Claims

The following claims are not supported by this branch:

```text
1. Source-diverse wrong-history self-identification under the current task.
2. Source-diverse delayed-history outcome necessity under the current task.
3. Using M1394/M1397 rows as a training corpus.
4. Claiming level3 anticipatory self-identification.
5. Continuing to tune the same M1394 rows as if more public-row sweeps are
   likely to change the conclusion.
```

The decisive negative is that wrong-warmup, same-recent wrong-warmup, and
delayed-warmup variants all remain at zero outcome-critical rows after the full
sweep.

## Failure Taxonomy Summary

Primary labels:

```text
scenario_sampling_failure
public_gate_overfit_risk
```

Explanation:

```text
scenario_sampling_failure:
  The source generator can materialize matched/bucketed rows, but the current
  reveal pressure does not create source-diverse outcome necessity for
  wrong-history or delayed-history interventions.

public_gate_overfit_risk:
  Repeatedly tuning against M1394/M1397 rows would risk optimizing a
  seed-139421 warmup-duration pocket rather than discovering a general
  history-necessity phenomenon.
```

Not primary:

```text
contract_violation: no evidence
training_instability: not applicable
proof_washout: not applicable
private_holdout_contamination: no private holdout used
```

## Public Gate Overfit Risk

Risk level:

```text
high_for_M1394_M1397_rows
```

Reason:

```text
The branch has now inspected and swept the full M1394 public warmup-latched
surface. The only warmup-history positives are seed-singleton margin-gap rows.
Any direct corpus export, threshold relaxation, or local row tuning would likely
learn the public diagnostic artifact.
```

The next branch must change the evidence axis, not just expand or tune the same
rows.

## Next Branch Decision

Open:

```text
paper_route_warmup_reveal_pressure_redesign
```

Goal:

```text
Design source generation that makes normal rollouts viable but near enough to
the emergency boundary that wrong/shortened/delayed warmup history can cause
source-diverse outcome gaps.
```

Design constraints:

```text
actor inputs remain P0 human-view;
hidden capability labels remain sampler/logging-only;
no oracle feasibility labels enter actor input;
current/recent-frame substitution must be explicitly controlled;
normal viability must be separated from near-boundary pressure;
source diversity must be pre-registered before corpus export or training.
```

Initial redesign directions:

```text
1. Reveal-pressure targeting:
   choose obstacle/reveal timing so normal margin is small but nonnegative,
   rather than sweeping broad successful margins.

2. Same-current pressure:
   prefer rows where current/recent observations are tightly matched, but
   warmup history or hidden state differs enough to change future margin.

3. Warmup stimulus strengthening:
   use low-risk natural road geometry or decel/curvature cues that expose
   braking/yaw/lateral authority before emergency reveal without giving actor
   an explicit target or mode label.

4. Branch guard:
   if the redesigned public source still produces only seed-singleton
   warmup-duration rows, stop and switch task family rather than tuning the same
   rows.
```

Next milestone:

```text
m1399-paper-route-warmup-reveal-pressure-redesign
```

M1399 should be a design milestone, not training. It should define the exact
source-generation changes, matching metrics, near-boundary normal-viability
rules, and stop conditions for the next implementation.

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
