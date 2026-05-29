# M1575 Paper-Route History-Sensitive Active-Set Mining Design

## Summary

M1575 designs the next bounded public miner.

Decision:

```text
history_sensitive_active_set_mining_design_admit_bounded_implementation
```

M1573 proved that the history-intervention harness is live, but its positive
history signal was concentrated in `t5_near_boundary_warmup`. The high-speed
third-source and late-reveal diagnostic anchors stayed history-null even though
their donor hidden and response/action distances were not weak. Therefore the
next miner must not assume that local forced-control flip anchors are also
history-sensitive anchors.

The new active-set definition is:

```text
an anchor is active for this branch only if history surgery changes the
closed-loop continuation outcome or terminal margin more than current-frame
substitution controls do.
```

This is design only. It does not run simulator traces, history interventions,
candidate materialization, corpus export, training, PPO, promotion, private
holdout, actor-input changes, or level3 self-identification claims.

## Input Artifacts

M1576 should use only public branch artifacts and the fixed P0 public actor:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
runs/m1570_targeted_third_source_flip_anchor_smoke/source_spec_rows.csv
runs/m1570_targeted_third_source_flip_anchor_smoke/recoverable_active_anchor_rows.csv
runs/m1573_source_diverse_flip_anchor_history_intervention_smoke/summary.json
runs/m1573_source_diverse_flip_anchor_history_intervention_smoke/history_intervention_rows.csv
```

It may reuse implementation mechanics from:

```text
src/autodrift/targeted_third_source_flip_anchor.py
src/autodrift/source_diverse_flip_anchor_history_interventions.py
src/autodrift/calibrated_terminal_boundary_history_interventions.py
```

but the output schema must be M1576-specific and must keep history-sensitive
selection separate from training-corpus export.

## Source Generation

The miner should generate candidate source specs from public simulator knobs
already supported by the P0 single-track simulator:

```text
t5_near_boundary_warmup
t5_boundary_axis_retarget
t5_high_speed_close_obstacle
late_reveal_boundary
curved_boundary_obstacle
low_authority / AEB-infeasible variants already exposed by the current hooks
```

Do not add wheel-puncture, single-wheel grip loss, half-shaft failure, or other
four-wheel fault labels in M1576. Those require a higher-fidelity vehicle model
and should remain future simulator-fidelity work. For this branch, the point is
to mine history-sensitive anchors under the current deployable P0 observation
contract.

## Anchor Windows

M1576 should evaluate anchors before the terminal outcome is fixed:

```text
reveal
reveal_plus_4
decision_minus_24
decision_minus_16
decision_minus_8
decision
```

If multiple windows collapse to the same simulator step, de-duplicate by:

```text
calibration_id@anchor_step
```

The miner should report window-level summaries and must not let one window
dominate the accepted set.

## Candidate Replay

For every candidate anchor:

```text
1. Replay the fixed P0 public actor from reset to the anchor step.
2. Capture env state, observation, response/action frame, actor hidden,
   hidden_by_step, action, source-family metadata, and normal continuation.
3. Continue the normal branch for the same continuation horizon used by
   interventions.
4. Reject candidates with replay errors, guardrail violations, actor-contract
   violations, or already-terminal state at the anchor.
```

The actor input contract remains the 72-dim human-view no-wheel P0 frame.

## Donor Pairing

History-sensitive mining must use source-diverse donors, but donor distance
alone is not an acceptance criterion. M1573 showed that large donor hidden
distance does not guarantee outcome sensitivity.

For each target anchor, construct bounded donor pairs:

```text
same-window different-source donor;
different-window different-source donor;
nearest response/action donor from a different source;
nearest hidden donor from a different source;
contrasting-normal-outcome donor when available.
```

Donor ranking keys:

```text
different source_family required;
prefer same anchor_window, but keep at least one cross-window donor;
prefer contrasting normal outcome when available;
prefer small anchor-step distance for matched-current-state tests;
round-robin source families to prevent one donor family dominating.
```

Each accepted target should keep enough donor metadata to audit whether a null
result is caused by poor pairing or by genuine history insensitivity.

## Required Intervention Variants

Primary history variants:

```text
wrong_history_donor_hidden_at_anchor
donor_response_action_plus_hidden_from_anchor
```

Secondary history variants:

```text
delayed_hidden_8_at_anchor
delayed_hidden_16_at_anchor
```

Current-frame and control variants:

```text
donor_response_action_stream_from_anchor
reset_hidden_once_at_anchor
reset_hidden_every_step_from_anchor
zero_current_response_from_anchor
zero_action_history_from_anchor
zero_all_response_from_anchor
```

Controls are mandatory. A history-sensitive anchor is not accepted if the same
or larger outcome degradation is explained by zeroing current response/action
fields or by donor response/action stream without donor hidden.

## Acceptance Criteria

For each target-donor pair, compute:

```text
primary_history_gap =
  max terminal-margin degradation over primary history variants

primary_history_outcome_drop =
  any success drop or collision increase over primary history variants

best_control_gap =
  max terminal-margin degradation over current-frame/control variants

best_control_outcome_drop =
  any success drop or collision increase over current-frame/control variants

hidden_specific_gap =
  donor_response_action_plus_hidden gap
  - donor_response_action_stream gap
```

A pair is history-positive if:

```text
primary_history_gap >= 0.02
or primary_history_outcome_drop is true
```

and at least one of:

```text
primary_history_gap >= 1.25 * max(best_control_gap, 1e-6)
hidden_specific_gap >= 0.01
primary_history_outcome_drop is true and best_control_outcome_drop is false
```

An anchor is accepted as history-sensitive if at least one source-diverse donor
pair is history-positive and the anchor replay has clean guardrails.

Diagnostic labels:

```text
history_sensitive_clean:
  history-positive and controls do not dominate

history_sensitive_control_overlap:
  history-positive but controls also degrade; keep diagnostic, not clean

history_null:
  no primary history variant reaches threshold

control_substitution_dominated:
  controls reach threshold but primary history does not exceed controls

donor_mismatch_suspected:
  donor distances are small and no history/control effect appears

source_family_null:
  a family has adequate candidates and donors but zero history-sensitive anchors
```

## Public Gates For M1576

M1576 should pass public smoke gates only if:

```text
source_spec_count >= 240
anchor_candidate_count >= 192
replay_ok_anchor_count >= 96
donor_pair_count >= 128
intervention_row_count >= 768
history_sensitive_anchor_count >= 12
clean_history_sensitive_anchor_count >= 8
history_sensitive_source_family_count >= 2
history_sensitive_window_count >= 3
non_near_family_history_sensitive_count >= 4
high_speed_history_sensitive_count >= 1
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
history_sensitive_anchor_count >= 24
clean_history_sensitive_anchor_count >= 16
history_sensitive_source_family_count >= 3
history_sensitive_window_count >= 4
max_single_history_sensitive_family_share <= 0.50
non_near_family_history_sensitive_count >= 8
high_speed_history_sensitive_count >= 4
or late_reveal_history_sensitive_count >= 2
control_substitution_dominated_share <= 0.40
```

If public gates pass but evidence-quality fails, route to audit before any
materialization or training.

## Required Artifacts

M1576 should write:

```text
runs/m1576_history_sensitive_active_set_miner_smoke/source_spec_rows.csv
runs/m1576_history_sensitive_active_set_miner_smoke/anchor_candidate_rows.csv
runs/m1576_history_sensitive_active_set_miner_smoke/donor_pair_rows.csv
runs/m1576_history_sensitive_active_set_miner_smoke/history_intervention_rows.csv
runs/m1576_history_sensitive_active_set_miner_smoke/history_sensitive_anchor_rows.csv
runs/m1576_history_sensitive_active_set_miner_smoke/history_sensitive_source_family_summary.csv
runs/m1576_history_sensitive_active_set_miner_smoke/history_sensitive_window_summary.csv
runs/m1576_history_sensitive_active_set_miner_smoke/history_intervention_variant_summary.csv
runs/m1576_history_sensitive_active_set_miner_smoke/control_substitution_summary.csv
runs/m1576_history_sensitive_active_set_miner_smoke/guardrail_summary.csv
runs/m1576_history_sensitive_active_set_miner_smoke/summary.json
```

Do not write:

```text
training corpus;
checkpoint;
promotion artifact;
private-holdout result.
```

## Null Classification

M1576 must classify failures instead of only reporting failed gates:

```text
no_history_signal:
  history variants do not exceed threshold anywhere.

source_singleton_history_signal:
  positives exist but only one source family is active.

control_substitution_dominated:
  zero/current-frame controls explain most apparent history effects.

high_speed_late_null:
  near-boundary positives exist, but high-speed and late-reveal remain null.

donor_mismatch_likely:
  donor distances are systematically too small and null results are ambiguous.

guardrail_or_contract_failure:
  replay, actor contract, or forbidden-output guardrails fail.

source_diverse_history_sensitive_pass:
  source-diverse clean history-sensitive anchors are found.
```

## Follow-Up Logic

If M1576 passes public gates:

```text
M1577 audits source diversity, control substitution, high-speed/late behavior,
and whether a compact corpus export can be designed.
```

If M1576 fails because positives are source-singleton:

```text
M1577 audits scenario sampling failure and either routes to branch synthesis or
designs one bounded source-family repair.
```

If M1576 fails because controls dominate:

```text
M1577 audits current-frame substitution and blocks history claims.
```

If M1576 is history-null across families:

```text
M1577 should synthesize or pivot; do not keep adding narrow donor repairs.
```

## Guardrails

```text
history_interventions_executed: false in M1575
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
m1576-paper-route-history-sensitive-active-set-miner-implementation
```
