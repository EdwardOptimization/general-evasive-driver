# M1573 Paper-Route Source-Diverse Flip-Anchor History-Intervention Implementation

## Summary

M1573 implements and runs the bounded source-diverse history-intervention smoke
designed in M1572.

Decision:

```text
source_diverse_history_intervention_smoke_public_pass_evidence_narrow_route_to_audit
```

The implementation and public smoke gates pass: the runner executes all
intervention variants over the M1570 active set with clean guardrails. The
evidence-quality target fails because history-positive effects are concentrated
in one source family:

```text
t5_near_boundary_warmup
```

The high-speed third-source anchors and late-reveal diagnostic anchors remain
history-null under this smoke. The result must be audited before any repair,
materialization, corpus export, training, PPO, or promotion.

## Implementation

Added:

```text
src/autodrift/source_diverse_flip_anchor_history_interventions.py
tests/test_source_diverse_flip_anchor_history_interventions.py
```

The runner:

```text
loads the M1570 flip-anchor rows;
adds up to 8 diagnostic late_reveal_boundary recoverable non-flip anchors;
builds source-diverse donor pairs;
reconstructs M1570 CalibrationSpecs deterministically;
replays the fixed public actor to each anchor;
caches anchor replay states;
runs normal, wrong-history, donor-response/action, delayed, reset, zero-current,
zero-action-history, and zero-all variants;
writes intervention rows and grouped summaries.
```

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_source_diverse_flip_anchor_history_interventions.py -q
3 passed
```

Smoke command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_diverse_flip_anchor_history_interventions \
  --output-dir runs/m1573_source_diverse_flip_anchor_history_intervention_smoke \
  --continuation-steps 64
```

## Result

```text
target_anchor_count: 14
diagnostic_late_anchor_count: 8
all_target_anchor_count: 22
target_source_family_count: 3
target_window_count: 4
high_speed_target_anchor_count: 4
late_reveal_diagnostic_anchor_count: 8
donor_pair_count: 44
same_window_donor_pair_count: 40
contrasting_outcome_pair_count: 33
variant_count: 11
history_variant_count: 4
control_variant_count: 5
intervention_row_count: 484
wrong_history_row_count: 44
donor_response_action_row_count: 88
reset_zero_control_row_count: 220
anchor_replay_failure_count: 0
max_wrong_history_margin_gap: 0.388129872572502
max_donor_response_action_margin_gap: 0.3871693514623984
max_history_margin_gap: 0.388129872572502
max_control_margin_gap: 0.08767311490103724
control_to_history_gap_ratio: 0.22588602706600497
history_success_drop_count: 3
history_positive_source_family_count: 1
high_speed_history_positive_count: 0
late_reveal_history_positive_count: 0
late_reveal_control_positive_count: 0
passes_public_smoke_gates: true
passes_evidence_quality_targets: false
guardrail_violation_count: 0
history_interventions_executed: true
candidate_materialized: false
training_corpus_exported: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

Variant summary:

```text
wrong_history_donor_hidden_at_anchor:
  max_margin_gap_from_normal: 0.388129872572502
  success_drop_count: 0
  collision_increase_count: 2

donor_response_action_plus_hidden_from_anchor:
  max_margin_gap_from_normal: 0.3871693514623984
  success_drop_count: 3
  collision_increase_count: 5

donor_response_action_stream_from_anchor:
  max_margin_gap_from_normal: 0.014828593489239594
  success_drop_count: 0
  collision_increase_count: 0

zero_action_history_from_anchor:
  max_margin_gap_from_normal: 0.08767311490103724

zero_current_response_from_anchor / zero_all_response_from_anchor:
  max_margin_gap_from_normal: 0.04076085381699013
```

Source-family summary:

```text
late_reveal_boundary:
  max_history_margin_gap: 0.00015732624357789327
  max_control_margin_gap: 0.0005579428417092913
  history_positive_count: 0
  control_positive_count: 0

t5_boundary_axis_retarget:
  max_history_margin_gap: 0.0036921571655645913
  max_control_margin_gap: -0.0005715951900975291
  history_positive_count: 0
  control_positive_count: 0

t5_high_speed_close_obstacle:
  max_history_margin_gap: 0.002529000222704525
  max_control_margin_gap: 0.011666837639857874
  history_positive_count: 0
  control_positive_count: 0

t5_near_boundary_warmup:
  max_history_margin_gap: 0.388129872572502
  max_control_margin_gap: 0.08767311490103724
  history_positive_count: 20
  control_positive_count: 30
  history_success_drop_count: 3
```

## Interpretation

M1573 proves the intervention harness is live:

```text
all anchor replays succeed;
all variants execute;
wrong-history hidden and donor-plus-hidden can produce large outcome-relevant
margin gaps;
donor response/action stream alone remains much weaker than donor plus hidden;
guardrails stay clean.
```

But it does not establish source-diverse history necessity:

```text
history_positive_source_family_count: 1
high_speed_history_positive_count: 0
late_reveal_history_positive_count: 0
```

The current positive effect is concentrated in `t5_near_boundary_warmup`, which
was already one of the existing flip families before M1570. The high-speed
third-source anchors that made M1570 pass source-generation gates do not yet
show history-positive intervention effects.

Therefore M1573 is a public-pass / evidence-narrow result. It should route to
audit, not materialization or training.

## Failure Taxonomy

```text
scenario_sampling_failure
```

This is not an implementation failure. It is an evidence-quality failure: the
active set supports history-positive behavior only on one source family under
the current donor pairing and intervention design.

## Guardrails

```text
history_interventions_executed: true
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
m1574-paper-route-source-diverse-history-intervention-result-audit
```

M1574 should decide whether the next route is donor-pairing repair,
source-family-specific active-set repair, branch synthesis, or a smaller audit
of why high-speed third-source anchors are intervention-null.
