# M1482 Paper-Route Source-Diverse Pressure Replay Result Audit

## Summary

M1482 audits the M1481 source-diverse pressure bounded replay result.

Decision:

```text
source_diverse_pressure_replay_audit_positive_source_singleton_route_to_neighbor_viability_calibration_design
```

Failure type:

```text
scenario_sampling_failure
```

M1482 does not run replay, train, run PPO, promote, use private holdout, export
corpus, or change actor inputs.

## Audit Finding

M1481 succeeded as a replay smoke:

```text
actual_replay_rows: 252
actual_replay_unique_source_seeds: 5
actual_replay_unique_capability_pairs: 7
history_positive_rows: 12
control_positive_rows: 15
```

But the replay positives did not become source-diverse:

```text
history_positive_unique_source_seeds: 1
history_positive_unique_capability_pairs: 1
history_positive_unique_reveal_buckets: 1
history_positive_unique_variants: 1
```

All history positives remain:

```text
seed: 141901
capability_pair: brake_authority_drop->mass_cg_shift
variant: warmup_removed
```

Controls are also same-family:

```text
control_positive_rows: 15
control_positive_unique_source_seeds: 1
control_positive_unique_capability_pairs: 1
variants: zero_current_response, reset_hidden
```

## Neighbor-Source Diagnosis

The important split:

```text
original source rows: 36
original normal viable rows: 36
original history positives: 12
original control positives: 15

neighbor source rows: 216
neighbor normal viable rows: 66
neighbor normal failed rows: 150
neighbor history positives: 0
neighbor control positives: 0
```

Neighbor rows were present in replay, but most did not enter the correct
normal-viable near-boundary window. Some neighbor history rows showed positive
margin gaps, but their normal branch had already failed. Other neighbor rows
were too easy or had too little action/margin separation.

So the blocker is not missing proposal diversity. It is that the neighbor-source
pressure map does not yet calibrate normal viability and variant degradation at
the same time.

## Interpretation

Supported:

```text
The M1476/M1479 source-diverse candidate path can reach replay.
M1481 preserves actual replay diversity across 5 seeds and 7 capability pairs.
The original local surface remains live and produces stronger positives after
pressure retargeting.
```

Unsupported:

```text
source-diverse history-positive replay evidence exists.
M1481 positives are ready for corpus export.
M1481 supports training, promotion, paper-level self-identification, or level3
self-identification claims.
```

The next step should calibrate neighbor sources into a normal-viable
near-boundary band before trying another replay. It should not replay the same
pressure rows again unchanged.

## Next Design Requirement

M1483 should design neighbor normal-viability calibration:

```text
use M1481 actual replay rows;
separate original-source positives from neighbor-source failures;
rank neighbor rows by normal viability class:
  - too_hard: normal branch fails or margin < 0;
  - near_boundary: normal viable with small positive margin;
  - too_easy: normal viable but large margin or tiny gap;
retarget neighbor rows toward normal viable and margin-gap-sensitive windows;
keep original-source rows capped as diagnostics only;
keep zero-current/reset controls separate;
do not train, replay, export corpus, promote, or change actor inputs.
```

## Guardrails

M1482 guardrail status:

```text
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

## Next Route

Admit:

```text
m1483-paper-route-neighbor-viability-calibration-design
```
