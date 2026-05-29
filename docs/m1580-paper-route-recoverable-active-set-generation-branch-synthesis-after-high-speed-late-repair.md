# M1580 Paper-Route Recoverable Active-Set Generation Branch Synthesis

## Summary

M1580 synthesizes the `paper_route_recoverable_active_set_generation` branch
from M1570 through M1579.

Synthesis decision:

```text
pivot
```

The branch produced important assets:

```text
source-diverse local flip anchors;
a live history-intervention harness;
a history-sensitive miner that finds clean positive anchors;
evidence that current high-speed/late sources are not history-sensitive under
the fixed P0 actor.
```

But the branch should not continue as another active-set source repair. The
blocker moved from "find recoverable anchors" to:

```text
find matched-current / hidden-divergent source pairs first.
```

The next branch is:

```text
paper_route_history_pairability_source_generation
```

Its first task should design a pairability-first source miner. It must prove
that public simulator sources can produce matched-current hidden-divergent
pairs before any new history intervention, corpus export, materialization, PPO,
or promotion.

## Evidence Summary

M1570 produced a source-diverse local flip-anchor set:

```text
flip_anchor_source_family_count: 3
third_source_flip_anchor_count: 4
targeted_family_flip_anchor_count: 4
targeted_flip_family_counts:
  t5_high_speed_close_obstacle: 4
```

M1573 ran source-diverse history interventions over those anchors:

```text
target_anchor_count: 14
intervention_row_count: 484
max_history_margin_gap: 0.388129872572502
history_success_drop_count: 3
history_positive_source_family_count: 1
high_speed_history_positive_count: 0
late_reveal_history_positive_count: 0
passes_public_smoke_gates: true
passes_evidence_quality_targets: false
```

M1576 changed the selection criterion from local forced-control flip to
history-sensitive outcome degradation:

```text
history_sensitive_anchor_count: 32
clean_history_sensitive_anchor_count: 30
history_sensitive_source_family_count: 2
history_sensitive_window_count: 5
control_substitution_dominated_share: 0.083984375
high_speed_history_sensitive_count: 0
late_reveal_history_sensitive_count: 0
passes_public_smoke_gates: false
null_result_classification: high_speed_late_null
```

M1579 tried one bounded high-speed/late repair with a matched-current /
hidden-divergent donor screen:

```text
source_spec_count: 360
anchor_candidate_count: 384
replay_ok_anchor_count: 267
screen_rejected_count: 24894
matched_current_hidden_divergent_pair_count: 0
strict_matched_pair_count: 0
fallback_matched_pair_count: 0
intervention_row_count: 0
null_result_classification: matched_pair_shortfall
```

This changes the branch diagnosis. The problem is no longer just high-speed or
late source sampling. The current generator cannot reliably create the
pairability precondition needed for history-necessity tests.

## Supported Claims

The branch supports:

```text
the public P0 actor/input contract stayed intact;
source-diverse local active-set anchors can be generated;
the history-intervention harness is operational;
wrong-history/donor-plus-hidden interventions can cause large outcome changes
in some source families;
history-sensitive active-set mining finds cleaner positives than flip-anchor
selection alone;
positive history-sensitive anchors currently concentrate in
t5_near_boundary_warmup and t5_boundary_axis_retarget;
high-speed/late current-frame controls can matter even when wrong history does
not matter;
matched-current hidden-divergent pairability is now the prerequisite blocker.
```

## Unsupported Claims

The branch does not support:

```text
source-diverse paper-level history necessity;
high-speed history sensitivity;
late-reveal history sensitivity;
curved-source history sensitivity;
level3 anticipatory self-identification;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence.
```

## Falsified Claims

The branch falsified or weakened these working assumptions:

```text
local forced-control flip anchors are automatically history-sensitive;
large donor hidden distance alone is enough to create wrong-history outcome
degradation;
targeted high-speed local active-set anchors are enough to create high-speed
history evidence;
late-reveal recoverable anchors are enough to create late-reveal history
evidence;
more high-speed/late source pressure is useful without first checking
matched-current hidden-divergent pairability.
```

## Failure Taxonomy Summary

```text
scenario_sampling_failure
```

More precisely:

```text
source-family sampling failure in M1573/M1576;
matched-pairability failure in M1579.
```

This is not a code failure, not a training failure, and not an actor-input
contract failure.

## Public-Gate Overfit Risk

Risk is high if the project keeps repairing this branch.

Reasons:

```text
the branch has repeatedly produced useful local diagnostics but not the desired
source-diverse history evidence;
M1576 positives are real but still source-limited;
M1579 showed that a targeted high-speed/late repair can fail before any
intervention because the pairability precondition is absent;
relaxing M1579 screens after seeing the result would contaminate the gate.
```

The right control action is to pivot, not to continue narrow repair.

## Next Branch Decision

Pivot to:

```text
paper_route_history_pairability_source_generation
```

The first milestone should be design-only:

```text
m1581-paper-route-history-pairability-source-generation-design
```

The new branch should reverse the order:

```text
old order:
  recoverable/local active set -> donor history interventions -> discover
  pairability is absent

new order:
  matched-current hidden-divergent pairability -> then active-set and
  history-intervention tests
```

The new branch should pre-register pairability gates before any intervention:

```text
matched_current_hidden_divergent_pair_count;
strict and fallback pair counts;
source-family diversity;
window diversity;
hidden_l2 distribution;
response/action_l2 distribution;
current-frame substitution controls;
null classification if pairability is absent.
```

## Guardrails

```text
history_interventions_executed: false in M1580
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1581-paper-route-history-pairability-source-generation-design
```
