# M1409 Paper-Route Warmup Reveal Pressure Branch Synthesis

## Summary

M1409 synthesizes the M1399-M1408 warmup/reveal pressure branch because the
workflow cadence fired after M1408.

Synthesis decision:

```text
continue
```

Decision:

```text
warmup_reveal_pressure_synthesis_continue_to_staged_warmup_source_smoke
```

M1409 does not run source smoke, outcome interventions, training, PPO, promote,
use private holdout, export a training corpus, or change actor inputs.

## Evidence Summary

M1399 started the branch after M1397 showed source-narrow warmup-latched
outcomes. It proposed late reveal and near-boundary pressure.

M1400 source smoke:

```text
result_class: warmup_latched_structural_pass
source_rows: 1604
matched_or_bucketed_reveal_rows: 256
matched/bucketed unique_source_seeds: 23
matched/bucketed unique_capability_pairs: 16
matched/bucketed unique_reveal_buckets: 92
viable reveal steps: 64,72,80
```

M1401 outcome probe:

```text
result_class: warmup_latched_outcome_action_only
preferred_near_boundary_candidate_rows: 0
accepted_outcome_rows: 0
warmup_history_positive_rows: 0
action_critical_rows: 1464
```

M1402 audited M1401 and pivoted from late reveal alone to mild warmup stimulus.

M1403 designed figure-eight mild warmup stimulus with no actor input changes.

M1404 source smoke:

```text
result_class: warmup_latched_structural_pass
source_rows: 1528
matched_or_bucketed_reveal_rows: 282
matched/bucketed unique_source_seeds: 27
matched/bucketed unique_capability_pairs: 16
matched/bucketed unique_reveal_buckets: 101
viable reveal steps: 48,56,64
```

M1405 outcome probe:

```text
result_class: warmup_latched_outcome_reset_or_current_only
preferred_near_boundary_candidate_rows: 26
accepted_outcome_rows: 2
warmup_history_positive_rows: 0
accepted_reset_rows: 2
action_critical_rows: 1584
```

M1406 audited M1405 as near-boundary progress but history-outcome negative, then
pivoted to stronger pre-emergency stimulus design.

M1407 selected a conservative staged slot0 warmup gate design: show warmup gate
in the existing primary obstacle slot, then switch to the emergency obstacle.

M1408 implemented the disabled-by-default staged warmup gate API:

```text
focused tests: 44 passed
full tests: 1387 passed, 4 warnings
compileall: passed
actor_input_contract_changed: false
```

## Supported Claims

This branch supports the following limited claims:

```text
1. Late reveal and mild warmup configurations can materialize source-diverse
   matched/bucketed current reveal rows without actor-input changes.

2. Figure-eight mild warmup plus tighter obstacle pressure fixes the M1401
   preferred-window sparsity problem: preferred candidates rose from 0 to 26.

3. Passive curvature alone is not enough to create source-diverse
   wrong-warmup or delayed-history outcome necessity.

4. A disabled-by-default staged warmup gate API can be implemented while
   preserving default env behavior and the 72-dim P0 actor contract.
```

## Falsified Claims

The branch falsifies or fails to support:

```text
1. Source materialization alone is self-identification evidence.
   M1400/M1404 source rows did not imply outcome-history positives.

2. Strong action deltas are sufficient.
   M1401 and M1405 both had many action-critical rows but no
   warmup-history-positive outcome rows.

3. Passive figure-eight warmup is enough.
   It created near-boundary candidates but only reset-hidden high-margin
   accepted rows.

4. M1405 admits training or corpus export.
   It has zero warmup-history-positive rows and two reset-only accepted rows
   from one seed.
```

No level3 self-identification claim is supported.

## Failure Taxonomy Summary

Observed failure types:

```text
objective_overfit / public-row overfit risk:
  repeated public source/outcome probes can tune around fixed rows without
  proving history necessity.

scenario_sampling_failure:
  late reveal alone produced no preferred near-boundary candidates in M1401.

metric_artifact:
  source materialization and action L2 deltas looked promising but did not
  transfer to clearance/success gaps.

behavior_regression risk:
  training from reset-only rows would push generic recurrent robustness rather
  than wrong-history self-ID.
```

Not observed in this branch:

```text
training_instability
contract_violation
private_holdout_contamination
promotion_gate_failure
```

## Public Gate Overfit Risk

Risk is medium-to-high if the branch continues with only radius/width/distance
tweaks:

```text
M1400 and M1404 source surfaces are public and already probed.
M1401 and M1405 outcome probes are public and negative for self-ID.
Continuing the same grids would likely optimize action-only or reset-only
public effects.
```

Risk is acceptable for one staged warmup source smoke because M1408 adds a new
task mechanism:

```text
new API: staged slot0 warmup gate
new evidence axis: measurable warmup gate command-response evidence
guardrail: source smoke only before outcome probing
guardrail: no corpus export or training from source materialization
```

## Next Branch Decision

Decision:

```text
continue
```

Next milestone:

```text
m1410-paper-route-staged-warmup-gate-source-smoke
```

M1410 is admitted only as no-training source smoke. It should:

```text
1. extend source smoke reporting with warmup gate diagnostics;
2. create staged warmup gate configs;
3. run source smoke against M1362 alpha 0.1;
4. report source diversity, matched/bucketed rows, reveal-step split, and
   warmup action/response evidence diagnostics.
```

M1410 must not:

```text
run outcome interventions
train
run PPO
promote
use private holdout
export a corpus
change actor inputs
claim self-identification from source materialization
```

Stop after M1410 if:

```text
source reconstruction fails;
matched/bucketed rows are sparse;
warmup gate action/response evidence is weak;
warmup gate causes source collapse or early termination;
source diversity is seed-singleton or pair-singleton.
```

Only if M1410 source smoke passes should a later outcome probe be considered.

## Guardrails

```text
source_smoke_started: false
outcome_probe_started: false
training_started: false
evaluation_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```
