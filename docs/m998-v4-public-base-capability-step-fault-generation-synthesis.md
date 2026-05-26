# M998 V4 Public Base Capability-Step Fault Generation Synthesis

## Purpose

M998 synthesizes M989-M997 before opening any temporal objective branch.

This is a process milestone only. It does not train, run PPO, promote a
checkpoint, use private holdout, or change actor inputs.

## Evidence Summary

The branch started after M988 falsified config-only global extreme scenario
mining as a source-diverse wrong-history proof generator.

M989-M990:

```text
M989 designs hidden capability-step/fault events using the existing
extreme_dynamics_scenario_corpus harness.

M990 smoke passes:
  scenarios: 832
  snapshots: 3289
  matched_pairs: 768
  accepted wrong-history rows: 2
  reset-only rows: 132
```

M991-M992:

```text
M991 scales to:
  scenarios: 3328
  snapshots: 16393
  matched_pairs: 4096
  accepted wrong-history rows: 0
  reset-only rows: 1380

M992 audits the reset-only rows:
  wrong-history action gaps mostly near zero
  reset-hidden action/margin gaps large
```

M993-M995:

```text
M993 designs trace-window sequence interventions.

M994 runs the probe:
  result_class: sequence_temporal_history_positive
  accepted_sequence_rows: 277
  accepted_temporal_sequence_rows: 277
  accepted_cross_fault_sequence_rows: 0
  unique_temporal_accepted_fault_pairs: 9
  unique_temporal_accepted_seeds: 17

M995 audits the claim:
  positive: temporal-history dependence
  blocked: cross-fault wrong-history self-identification
```

M996-M997:

```text
M996 designs exact-auditable temporal sequence corpus export.

M997 implements it:
  row_count: 277
  positive_row_count: 277
  diagnostic_row_count: 4608
  unique_positive_fault_pairs: 9
  unique_positive_seeds: 17
  max_fault_pair_fraction: 0.191336
  delayed_capability_history_positive_rows: 24
  reset_then_warm_history_positive_rows: 253
  tensor_sanity_passed: true
  replay_sanity_passed: true
  exact_sanity_passed: true
  source_diversity_passed: true
  actor_parameters_changed: false
```

## Supported Claims

The branch supports these claims:

```text
1. The current M974 public base can be evaluated under hidden capability-step
   fault events without actor-input contract changes.

2. Larger capability-step source waves do not reproduce the sparse M990
   cross-fault wrong-history positives.

3. The policy has broad reset-hidden sensitivity under capability-step events.

4. Sequence-level temporal disruptions expose outcome-relevant temporal-history
   dependence.

5. That temporal evidence is source-diverse enough for a corpus:
   277 rows, 9 fault pairs, 17 seeds, max pair fraction below 0.25.

6. The temporal evidence can be exported into exact-auditable tensors with
   replay/action sanity and no-update log-prob sanity passing.
```

The most important technical result is not a new driver checkpoint. It is a
clean corpus and exact evaluation surface for temporal-history dependence under
capability-step events.

## Falsified Claims

The branch falsifies or blocks these claims:

```text
1. The capability-step source wave already proves source-diverse cross-fault
   wrong-history self-identification.

2. Single hidden-state swap is sufficient to expose wrong-history outcome
   sensitivity for the current M974 public base.

3. Cross-fault response/action-response mismatch variants from M994 are
   positive targets.

4. Reset-only sensitivity should be counted as cross-fault proof.

5. M997 corpus evidence justifies PPO or actor training without a separate
   objective design.

6. Current single-track dynamics support true per-wheel puncture, half-shaft
   failure, or corner-specific brake-loss claims.
```

## Failure Taxonomy Summary

The dominant failure mode is not training instability or behavior regression.
No training occurs in this branch.

Observed failure categories:

```text
scenario_sampling_failure:
  M991 scales source coverage but cross-fault accepted rows drop to zero.

metric_artifact:
  M994 initially could be overread as cross-fault positive; M995 corrects the
  taxonomy and separates temporal positives from cross-fault zero variants.

none:
  M997 export itself passes tensor, replay, exact, and source-diversity sanity.
```

The important negative result is that current cross-fault pair construction is
too compatible to create outcome-sensitive wrong-history evidence, even when
capability-step events exist.

## Public Gate Overfit Risk

Risk level:

```text
moderate
```

Reasons:

```text
The M997 corpus is public and derived from M991/M994 artifacts.
The corpus is source-diverse by seed and fault pair, but variant-imbalanced:
  reset_then_warm_history: 253
  delayed_capability_history: 24
No private holdout has been used.
No paper-level generalization claim is supported.
```

Mitigations already in place:

```text
row_weight balances variant and fault-pair frequency
diagnostic rows are separated from positive targets
cross-fault zero rows cannot be promoted to positives
exact no-update sanity is separate from future objective training
```

Required later before promotion/paper claims:

```text
fresh temporal-history corpus refresh
fresh scenario distribution gate
memory/ablation gates using reset, delayed, zero-command, and wrong-history
private holdout only after objective behavior is stable
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Close:

```text
v4_public_base_capability_step_fault_generation
```

Open:

```text
v4_public_base_temporal_sequence_objective
```

The immediate next task should not be PPO. It should design an exact objective
over the M997 corpus:

```text
M999:
  temporal sequence objective design
```

The objective design should:

```text
use normal uninterrupted history as the preferred branch;
use disrupted temporal history only for preference/separation diagnostics;
avoid training the variant branch toward degraded actions;
use row_weight;
keep cross-fault rows diagnostic-only;
define exact no-update baseline metrics before any actor update;
require replay/public proof gates before any promotion.
```

Cross-fault generation redesign remains useful later, but it should not block
the temporal objective branch. The branch has enough temporal-history evidence
to continue, and it has enough negative cross-fault evidence to prevent
overclaiming.

## Final Decision

```text
capability_step_fault_generation_synthesis_open_temporal_sequence_objective
```

Next:

```text
m999-v4-public-base-temporal-sequence-objective-design
```
