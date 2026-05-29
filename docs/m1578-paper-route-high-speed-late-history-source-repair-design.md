# M1578 Paper-Route High-Speed/Late History-Source Repair Design

## Summary

M1578 designs one bounded repair for the M1576 high-speed/late null.

Decision:

```text
high_speed_late_history_source_repair_design_admit_bounded_implementation
```

The repair target is narrow and explicit:

```text
find high-speed or late-reveal anchors where wrong-history or donor-plus-hidden
interventions degrade closed-loop outcome more than current-frame controls.
```

This design does not relax the M1576 gates. It changes source generation and
donor screening so the next implementation tests a more plausible history-use
condition:

```text
matched current response/action;
divergent hidden history;
high-speed or late-reveal emergency context;
current-frame controls included for every accepted row.
```

This is design only. It does not run simulator traces, history interventions,
candidate materialization, corpus export, training, PPO, promotion, private
holdout, actor-input changes, or level3 self-identification claims.

## Why A Repair Is Still Justified

M1576 did not fail because the miner was dead. It found:

```text
clean_history_sensitive_anchor_count: 30
history_sensitive_source_family_count: 2
history_sensitive_window_count: 5
control_substitution_dominated_share: 0.083984375
```

The blocker is source-specific:

```text
t5_high_speed_close_obstacle primary_history_gap max: 0.006224602548898783
late_reveal_boundary primary_history_gap max: 0.009707924566951132
```

Both families had strong current-frame control effects:

```text
high-speed max control gap: 0.31220594475079233
late-reveal max control gap: 0.2646042118514824
```

So the current source pool contains high-speed/late rows where the actor reacts
to current-frame perturbations, but not rows where wrong hidden history changes
the continuation. The next repair should not add more generic local-control
flip anchors. It should generate matched-current, hidden-divergent
high-speed/late pairs.

## Source Repair Scope

M1579 should add a new implementation module, not modify the main actor or
existing M1576 artifacts:

```text
src/autodrift/high_speed_late_history_source_repair.py
tests/test_high_speed_late_history_source_repair.py
```

It may reuse:

```text
targeted_source_specs;
CalibrationMode / _retarget_hook_spec;
build_anchor_candidates;
replay_to_anchor;
run_intervention_variant;
M1576 history-sensitive pair classifier.
```

The implementation must remain P0-compatible and no-wheel:

```text
no mu / tire / brake / actuator hidden params in actor input;
no slip / wheel / force inputs;
no oracle labels;
no path reference;
no TTC or required clearance.
```

## New Source Families

M1579 should construct target-heavy source specs for two repair families:

```text
hs_history_pressure
late_history_pressure
```

These are artifact source labels only. They must not enter actor input.

### High-Speed History Pressure

High-speed modes should keep the scene hard enough for current-frame control to
matter, but create more pre-decision history evidence:

```text
speed_shift: 4.0 to 6.0
distance_scale: 0.62 to 0.82
half_width_shift: 0.45 to 0.75
reveal_delta: -8, -4, 0, 4
low_authority_band: true on at least half the modes
require_aeb_infeasible: true on at least one third of modes
```

Candidate mode examples:

```text
hs_hist_early_reveal_low_authority
hs_hist_close_faster_aeb
hs_hist_wide_boundary_pressure
hs_hist_matched_current_low_authority
hs_hist_reveal_to_decision_gap
```

### Late-Reveal History Pressure

Late-reveal modes should keep obstacle reveal late, but avoid anchors that are
already terminally fixed at reveal:

```text
speed_shift: 2.0 to 5.0
distance_scale: 0.70 to 0.92
half_width_shift: 0.30 to 0.70
reveal_delta: 6, 8, 10, 12
low_authority_band: true on at least half the modes
require_aeb_infeasible: true on at least one third of modes
```

Candidate mode examples:

```text
late_hist_reveal_plus_window
late_hist_low_authority_moderate
late_hist_aeb_wide
late_hist_not_yet_fixed_boundary
late_hist_speed_pressure
```

## Anchor Windows

M1579 should add windows around reveal and earlier decision pressure:

```text
reveal
reveal_plus_2
reveal_plus_4
reveal_plus_8
decision_minus_32
decision_minus_24
decision_minus_16
decision_minus_8
decision
```

De-duplicate by:

```text
calibration_id@anchor_step
```

The goal is not simply more anchors. The goal is to catch high-speed/late rows
where history can still change the maneuver before the continuation is fixed.

## Matched-Current / Hidden-Divergent Donor Screen

M1576 used source-diverse donors but did not require matched current response.
M1579 should add a donor screen before expensive continuation:

```text
target_donor_response_action_l2 <= 0.55
target_donor_hidden_l2 >= 3.0
different source_family required
same anchor_window preferred
anchor step distance <= 16 preferred
```

If too few pairs satisfy the strict screen, allow a bounded fallback:

```text
response_action_l2 <= 0.75
hidden_l2 >= 4.0
```

The screen should report both strict and fallback pair counts. Pairs that fail
both screens should not be used for acceptance, even if they have large donor
distance, because they do not test the desired matched-current hidden-history
condition.

## Interventions

Required primary history variants:

```text
wrong_history_donor_hidden_at_anchor
donor_response_action_plus_hidden_from_anchor
```

Required controls:

```text
donor_response_action_stream_from_anchor
reset_hidden_once_at_anchor
reset_hidden_every_step_from_anchor
zero_current_response_from_anchor
zero_action_history_from_anchor
zero_all_response_from_anchor
```

Secondary diagnostics:

```text
delayed_hidden_8_at_anchor
delayed_hidden_16_at_anchor
```

Acceptance must stay M1576-compatible:

```text
primary_history_gap >= 0.02
or primary_history_outcome_drop
```

and one of:

```text
primary_history_gap >= 1.25 * max(best_control_gap, 1e-6)
hidden_specific_gap >= 0.01
primary_history_outcome_drop and not best_control_outcome_drop
```

## Public Gates For M1579

M1579 should pass public smoke gates only if:

```text
source_spec_count >= 240
anchor_candidate_count >= 256
replay_ok_anchor_count >= 128
matched_current_hidden_divergent_pair_count >= 96
intervention_row_count >= 768
high_speed_or_late_history_sensitive_anchor_count >= 8
clean_high_speed_or_late_history_sensitive_anchor_count >= 6
high_speed_history_sensitive_count >= 4
or late_reveal_history_sensitive_count >= 4
history_sensitive_window_count >= 3
control_substitution_dominated_share <= 0.40
guardrail_violation_count == 0
candidate_materialized == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
training_corpus_exported == false
```

Evidence-quality targets:

```text
high_speed_or_late_history_sensitive_anchor_count >= 16
clean_high_speed_or_late_history_sensitive_anchor_count >= 12
high_speed_history_sensitive_count >= 6
late_reveal_history_sensitive_count >= 4
history_sensitive_window_count >= 4
matched_current_hidden_divergent_pair_count >= 160
control_substitution_dominated_share <= 0.30
```

If public gates pass but evidence-quality fails, route to audit before any
materialization.

## Required Artifacts

M1579 should write:

```text
runs/m1579_high_speed_late_history_source_repair_smoke/source_spec_rows.csv
runs/m1579_high_speed_late_history_source_repair_smoke/anchor_candidate_rows.csv
runs/m1579_high_speed_late_history_source_repair_smoke/matched_donor_pair_rows.csv
runs/m1579_high_speed_late_history_source_repair_smoke/history_intervention_rows.csv
runs/m1579_high_speed_late_history_source_repair_smoke/history_sensitive_anchor_rows.csv
runs/m1579_high_speed_late_history_source_repair_smoke/history_sensitive_source_family_summary.csv
runs/m1579_high_speed_late_history_source_repair_smoke/history_sensitive_window_summary.csv
runs/m1579_high_speed_late_history_source_repair_smoke/control_substitution_summary.csv
runs/m1579_high_speed_late_history_source_repair_smoke/guardrail_summary.csv
runs/m1579_high_speed_late_history_source_repair_smoke/summary.json
```

Do not write:

```text
training corpus;
checkpoint;
promotion artifact;
private-holdout result.
```

## Stop And Synthesis Rule

This repair is allowed exactly once.

If M1579 fails because high-speed and late-reveal remain null:

```text
M1580 must audit the result;
then route to branch synthesis unless the audit identifies a new concrete
source-generation bug rather than another sampling preference.
```

If M1579 passes:

```text
M1580 still audits before any corpus export or materialization.
```

No direct PPO, candidate materialization, or training is admitted by this
design.

## Guardrails

```text
history_interventions_executed: false in M1578
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
m1579-paper-route-high-speed-late-history-source-repair-implementation
```
