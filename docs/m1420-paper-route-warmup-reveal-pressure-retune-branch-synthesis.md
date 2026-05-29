# M1420 Paper-Route Warmup Reveal Pressure Retune Branch Synthesis

## Summary

M1420 synthesizes the staged warmup gate work from M1410 through M1419 before
any outcome probe, further retune, training, or corpus export.

Decision:

```text
warmup_reveal_pressure_retune_synthesis_promote_to_staged_warmup_outcome_validation
```

Workflow synthesis decision:

```text
promote_to_next_branch
```

M1420 does not run source smoke, outcome interventions, train, run PPO, promote
a checkpoint, use private holdout, export a training corpus, or change actor
inputs.

## Evidence Summary

The branch made three concrete advances.

First, staged warmup gate source materialization is real:

```text
M1410 source_rows: 1690
M1410 matched/bucketed rows: 298
M1410 matched/bucketed seeds: 31
M1410 matched/bucketed capability pairs: 16
```

Second, staged warmup can create sparse outcome-relevant history effects:

```text
M1412 warmup_history_positive_rows: 14
M1412 accepted_history_unique_source_seeds: 3
M1412 accepted_history_unique_capability_pairs: 7
M1412 clear_stratum_warmup_history_positive_rows: 10
M1412 collision_stratum_warmup_history_positive_rows: 4
M1412 wrong_warmup_history_same_reveal_positive_rows: 0
```

Third, the retuned M1419 source fixes the main M1417 invasiveness problem while
preserving source volume and warmup evidence:

```text
M1417 matched/bucketed collision share: 0.544000
M1419 matched/bucketed collision share: 0.293651

M1417 clear + clear_low rows: 114
M1419 clear + clear_low rows: 178

M1419 source_rows: 1714
M1419 matched/bucketed rows: 252
M1419 matched/bucketed capability pairs: 16
M1419 matched/bucketed reveal buckets: 101
M1419 warmup_response_history_l2_p95: 0.050344
M1419 warmup_action_history_l2_p95: 0.019332
```

M1419 missed one source-diversity gate:

```text
required matched/bucketed unique_source_seeds: >= 28
observed matched/bucketed unique_source_seeds: 27
```

This miss is real and must stay visible.

## Supported Claims

Supported:

```text
staged warmup gate is a viable public source mechanism;
M1419 reduces warmup-gate invasiveness versus M1417;
M1419 preserves warmup command-response evidence;
M1419 is good enough for one no-training public outcome probe;
the next probe must remain collision/clear-stratified.
```

The one-seed miss is acceptable only for a no-training public outcome probe
because:

```text
1. no private holdout is used;
2. no training or corpus export is allowed;
3. outcome probing is diagnostic, not promotion;
4. source diversity is only one seed below threshold;
5. all other source/warmup/invasiveness gates pass.
```

## Falsified Claims

Not supported:

```text
M1419 is a fully clean source pass;
source materialization proves history necessity;
warmup evidence proves self-identification;
wrong-warmup history is outcome-critical;
staged warmup source rows are ready for training;
M1419 is paper-level evidence by itself;
GRU recurrent-belief advantage has been proven.
```

The current strongest claim remains below level3:

```text
level2_history_encoded_reactive
```

## Failure Taxonomy Summary

Observed failure types in this branch:

```text
scenario_sampling_failure:
  M1415 produced zero source rows under an over-constrained obstacle filter.
  M1419 missed the matched/bucketed source-seed threshold by one.

history_sparse_not_collision_only_but_seed_thin:
  M1412 produced 14 warmup-history positives from 3 seeds.
  The positives were not collision-only, but were too sparse.

source_viable_but_invasive:
  M1410 and M1417 produced source rows with too much warmup-gate collision
  pressure.
```

No evidence of these failures occurred in M1410-M1419:

```text
contract_violation
training_instability
private_holdout_contamination
promotion_gate_failure
actor_input_contract_changed
```

## Public Gate Overfit Risk

Public-gate overfit risk is medium.

Reasons:

```text
M1410-M1419 involved several retunes on public source diagnostics;
M1419 misses one pre-registered source-diversity threshold;
M1412 outcome positives were seed-thin;
wrong-warmup variants have remained zero so far.
```

Mitigations:

```text
do not train from M1419;
do not export a corpus from M1419;
do not use private holdout;
run only one no-training public outcome probe;
preserve collision/clear/source strata in every outcome artifact;
route to audit after the outcome probe before any further run.
```

## Next Branch Decision

The warmup/reveal pressure retune branch has done enough source design work.
Another local source retune would be a narrow loop.

M1420 promotes to a new branch:

```text
paper_route_staged_warmup_outcome_validation
```

Next milestone:

```text
m1421-paper-route-m1419-source-collision-stratified-outcome-probe
```

M1421 should run a no-training outcome probe over M1419 matched/bucketed rows:

```text
candidate_rows: runs/m1419_warmup_gate_invasiveness_retune_source_smoke/matched_or_bucketed_rows.csv
config: configs/m1419_warmup_gate_invasiveness_retune_source_wave.json
run_dir: runs/m1421_m1419_source_collision_stratified_outcome_probe
```

M1421 must report:

```text
warmup-history-positive rows;
accepted history seeds, capability pairs, and reveal buckets;
wrong_warmup_history_same_reveal positives;
same_recent_wrong_warmup_history positives;
reset and zero-current controls;
clear / clear_low_margin / collision strata;
near-boundary strata;
normal failed rows and action-critical rows.
```

M1421 does not admit training, PPO, promotion, private holdout, corpus export, or
actor-input expansion. It must route to an audit before any further experiment.
