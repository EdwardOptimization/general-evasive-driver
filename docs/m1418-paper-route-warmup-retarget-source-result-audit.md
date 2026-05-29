# M1418 Paper-Route Warmup Retarget Source Result Audit

## Summary

M1418 audits the M1417 repaired warmup retarget source smoke before any outcome
probe or training.

Decision:

```text
warmup_retarget_source_audit_admit_warmup_gate_invasiveness_retune_source_smoke
```

M1418 does not run source smoke, outcome interventions, train, run PPO, promote,
use private holdout, export a training corpus, or change actor inputs.

## What Passed

M1417 repaired the M1415 sampling failure. Source materialization is now strong:

```text
source_rows: 1630
matched_current_rows: 78
bucketed_current_rows: 198
matched_or_bucketed_reveal_rows: 250
finite_metric_rows: 1630
rejected_rows: 4898
```

Matched/bucketed source diversity is sufficient for another public source smoke:

```text
unique_source_seeds: 33
unique_capability_pairs: 16
unique_preferred_fault_families: 9
unique_wrong_fault_families: 9
unique_reveal_buckets: 90
max_single_seed_share: 0.128000
max_single_capability_pair_share: 0.120000
```

Warmup command-response evidence is also present:

```text
warmup_gate_visible_rows: 250 / 250
warmup_evidence_rows: 250 / 250
warmup_response_history_l2_p95: 0.070585
warmup_action_history_l2_p95: 0.020763
```

These pass the M1416 source, diversity, and warmup-evidence gates.

## What Failed

M1417 misses the pre-registered matched/bucketed invasiveness gates:

```text
matched/bucketed warmup_gate_collision_share: 0.544000
matched/bucketed collision rows: 136 / 250
matched/bucketed clear rows: 100
matched/bucketed clear_low_margin rows: 14
clear + clear_low_margin rows: 114
```

The failed thresholds were:

```text
warmup_gate_collision_share <= 0.50
clear + clear_low_margin rows >= 120
```

This is not a model or actor-contract failure. It is a scenario-design failure:
the source task is now sampleable and produces command-response history, but the
warmup gate still over-pressures the matched/bucketed subset.

## Interpretation

M1417 should not be routed to outcome probing yet. The failed invasiveness gates
would mix useful clear/low-margin source cases with too many warmup-gate
collision cases, making any downstream outcome-positive or outcome-negative
result hard to interpret.

The miss is narrow enough to justify one focused retune:

```text
collision share: 0.544000  # threshold 0.50
clear + clear_low rows: 114  # threshold 120
```

The retune should preserve the successful M1417 obstacle sampling repair and
change only the warmup gate geometry to reduce collision pressure.

## Route Decision

M1418 admits one no-training source smoke:

```text
m1419-paper-route-warmup-gate-invasiveness-retune-source-smoke
```

The M1419 retune should preserve:

```text
obstacle.distance_range: [4.0, 20.0]
obstacle.half_width_range: [0.90, 1.65]
obstacle.max_threshold_score: 0.50
warmup_gate.reveal_step: 2
warmup_gate.max_active_steps: 44
warmup_gate.finish_pass_distance: 1.5
```

It should retune only:

```text
warmup_gate.distance_range: [12.0, 20.0]
warmup_gate.lateral_offset_range: [-2.6, 2.6]
warmup_gate.half_width_range: [0.20, 0.35]
```

M1419 must use the same source-level gates as M1417 plus the same invasiveness
thresholds. If M1419 still misses invasiveness or loses source/warmup evidence,
the next step should be branch synthesis before further local retuning.

## Guardrails

M1418 does not claim self-identification. Source materialization and warmup
command-response evidence only show that the task creates a plausible
history-conditioned diagnostic setup.

The next step must not:

```text
train
run PPO
run outcome interventions
promote
use private holdout
export a corpus
change actor inputs
claim recurrent-belief advantage
claim level3 self-identification
```
