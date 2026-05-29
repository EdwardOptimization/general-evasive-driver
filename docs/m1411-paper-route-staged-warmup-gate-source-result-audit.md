# M1411 Paper-Route Staged Warmup Gate Source Result Audit

## Summary

M1411 audits the M1410 staged warmup gate source smoke before any outcome
intervention.

Decision:

```text
staged_warmup_gate_source_audit_admit_collision_stratified_outcome_probe
```

M1411 does not run outcome interventions, train, run PPO, promote, use private
holdout, export a training corpus, or change actor inputs.

## Source Viability

M1410 is a clean no-training structural pass:

```text
result_class: warmup_latched_structural_pass
source_rows: 1690
matched_current_rows: 122
bucketed_current_rows: 228
matched_or_bucketed_reveal_rows: 298
finite_metric_rows: 1690
rejected_rows: 3206
```

The matched/bucketed rows are source-diverse:

```text
unique_source_seeds: 31
unique_capability_pairs: 16
unique_preferred_fault_families: 9
unique_wrong_fault_families: 9
unique_reveal_buckets: 105
max_single_seed_share: 0.134228
max_single_capability_pair_share: 0.117450
```

This passes the source viability bar for a public no-training outcome probe.

## Warmup Evidence

M1410 also adds the missing warmup evidence diagnostics:

```text
all rows:
  warmup_gate_visible_rows: 1690 / 1690
  warmup_evidence_rows: 1690 / 1690
  warmup_response_history_l2_mean: 0.058476
  warmup_response_history_l2_p95: 0.124635
  warmup_action_history_l2_mean: 0.018808
  warmup_action_history_l2_p95: 0.056336

matched/bucketed rows:
  warmup_gate_visible_rows: 298 / 298
  warmup_evidence_rows: 298 / 298
  warmup_response_history_l2_mean: 0.031943
  warmup_response_history_l2_p95: 0.057279
  warmup_action_history_l2_mean: 0.006515
  warmup_action_history_l2_p95: 0.015199
```

This is stronger than M1404/M1405 on source evidence. It still does not prove
history necessity; it only shows the task creates a real command-response
history signal before emergency reveal.

## Invasiveness Risk

The source is strong, but the warmup gate is not mild:

```text
all rows warmup_gate_collision_rows: 1070 / 1690
matched/bucketed warmup_gate_collision_rows: 190 / 298
```

The collision flag is diagnostic and does not terminate the episode. However,
the high rate means an unstratified outcome probe could overstate task quality
or mix two different mechanisms:

```text
strong-gate evidence:
  actor saw and responded to a close obstacle-like warmup stimulus.

mild-probing evidence:
  actor gathered response information without penetrating the warmup gate.
```

These must be separated before any claim expansion, corpus export, or training.

## Decision

M1411 admits one no-training outcome probe because M1410 source viability is
good and the probe is the next cheapest way to test whether the source creates
outcome-relevant history interventions.

The outcome probe must be collision-stratified. It should propagate source-row
warmup gate diagnostics into outcome rows and report at least:

```text
accepted rows by warmup_gate_collision source stratum;
accepted rows by warmup_gate_clearance_margin band;
normal-margin candidates by warmup gate collision stratum;
warmup-history-positive rows separately for collision-free and collision-heavy rows;
reset / zero-current accepted rows separately from true warmup-history variants.
```

M1411 does not admit training, corpus export, or promotion. If M1412 is positive
only in collision-heavy rows, the next route should be mild-gate retuning rather
than training. If M1412 is positive in collision-free or low-invasiveness rows,
the route can proceed to a stricter public outcome repeat.

## Next

Next milestone:

```text
m1412-paper-route-staged-warmup-gate-collision-stratified-outcome-probe
```

M1412 must:

```text
1. extend the outcome probe to preserve warmup gate diagnostics from source rows;
2. run no-training outcome interventions over M1410 matched/bucketed rows;
3. report collision-stratified outcome, margin, and variant summaries;
4. block training, PPO, corpus export, promotion, private holdout, and claim expansion.
```

Stop or retune if:

```text
accepted rows are zero;
accepted rows are reset-only/current-only again;
history-positive rows are seed-singleton;
history-positive rows appear only in high-collision source strata;
normal viable candidates collapse under staged warmup.
```
