# M1546 Paper-Route Calibrated Terminal-Boundary History-Intervention Design

## Summary

M1546 designs the calibrated terminal-boundary history-intervention route
admitted by M1545.

Decision:

```text
calibrated_terminal_boundary_history_intervention_design_admit_bounded_implementation
```

M1544 fixed the source-window problem by producing actual near-boundary
terminal rows. M1546 does not treat that as self-identification evidence.
Instead, it designs the next bounded public experiment: reconstruct the
calibrated hook specs, rerun measured traces with response/context vectors,
build matched current-state/scene pairs, and then run history interventions with
explicit reset/zero-current controls.

This is design only. It does not train, run PPO, promote, use private holdout,
export a training corpus, materialize candidates, change actor inputs, or claim
level3 self-identification.

## Problem Statement

M1544 accepted calibrated near-boundary rows:

```text
accepted_calibrated_row_count: 8
accepted_terminal_family_count: 4
decision_window_hit_count: 4
post_decision_window_hit_count: 5
max_single_terminal_family_share: 0.25
```

But M1544 artifacts are calibration artifacts, not intervention artifacts. The
bounded-runner snapshots do not store full response/context vectors, so they
cannot by themselves support matched current-state/scene pair claims.

The missing evidence link is:

```text
calibrated near-boundary terminal row
  -> measured response/context snapshot
  -> matched current-state/scene pair
  -> wrong-history or donor-history intervention changes terminal margin/outcome
  -> effect is not dominated by reset/zero-current controls
```

## Required Implementation Shape

M1547 should implement:

```text
src/autodrift/calibrated_terminal_boundary_history_interventions.py
tests/test_calibrated_terminal_boundary_history_interventions.py
```

The implementation should reuse M1544's deterministic calibration grid:

```text
source_seed: 1843
source_seed_count: 2
max_base_rows: 20
max_calibration_specs: 160
accepted_calibrated_rows: runs/m1544_terminal_boundary_task_sampling_calibration_smoke/accepted_calibrated_rows.csv
```

Steps:

```text
1. Rebuild the same M1544 calibration specs.
2. Filter specs to accepted calibration_id values from M1544.
3. Rerun fixed-policy measured traces that include response/context vectors.
4. Capture decision and post-decision snapshots for accepted rows.
5. Build matched pairs with scene/current-state distance gates.
6. Replay from the calibrated anchor and run intervention variants.
7. Write measured, pair, intervention, variant, and guardrail summaries.
8. Route to audit before any materialization or training.
```

## Anchor Semantics

Use calibrated window type to select anchors:

```text
decision_window_hit -> decision anchor
post_decision_window_hit -> first post-decision snapshot that enters the post-decision window
both hits -> run both anchors but summarize separately
```

If implementation cannot recover the exact post-decision hit step from M1544
snapshots, it must recompute it during the measured-trace rerun from the same
calibrated hook spec. Do not infer it from metadata alone.

## Matched Pair Gates

Pairs must be built from measured response/context snapshots, not from terminal
family labels alone.

Acceptance thresholds:

```text
max_scene_context_distance: 0.12
max_current_ego_distance: 0.12
min_first_action_l2: 0.04
min_terminal_margin_gap: 0.02
different_source_family: required
same_or_compatible_window_kind: required
accepted_pair_count >= 4
accepted_source_family_edge_count >= 3
max_single_pair_source_edge_share <= 0.50
```

Because the calibrated set is small, the first implementation may allow
decision/post-decision compatible pairs, but it must report:

```text
decision_decision_pair_count
post_post_pair_count
decision_post_pair_count
```

## Intervention Variants

Run the same core intervention families used in M1534/M1538, adapted to
calibrated hook specs:

```text
normal
reset_hidden_once_at_anchor
reset_hidden_every_step_from_anchor
zero_current_response_from_anchor
zero_action_history_from_anchor
delayed_hidden_8_at_anchor
delayed_hidden_16_at_anchor
wrong_history_donor_hidden_at_anchor
donor_response_action_stream_from_anchor
donor_response_action_plus_hidden_from_anchor
```

Keep these channels separate:

```text
history: wrong_history_donor_hidden_at_anchor, donor_response_action_plus_hidden_from_anchor
stream-only: donor_response_action_stream_from_anchor
memory timing: delayed_hidden_8_at_anchor, delayed_hidden_16_at_anchor
controls: reset_hidden_*, zero_current_response_from_anchor, zero_action_history_from_anchor
```

## Pass / Fail Gates

Measured trace gates:

```text
accepted_calibrated_source_count >= 8
measured_trace_count >= 8
measured_snapshot_count >= 16
measured_trace_family_count >= 4
guardrail_violation_count == 0
```

Pair gates:

```text
accepted_pair_count >= 4
accepted_source_family_edge_count >= 3
max_single_pair_source_edge_share <= 0.50
anchor_replay_failure_rate <= 0.05
```

History-positive gates:

```text
terminal_wrong_history_positive_target_sides >= 2
or
terminal_donor_plus_hidden_positive_target_sides >= 2
or
terminal_wrong_or_donor_success_drop_count >= 1
```

Positive threshold:

```text
terminal_margin_gap_from_normal >= 0.02
```

Control check:

```text
terminal_control_to_history_gap_ratio <= 4.0
```

If pairs cannot be formed, classify as:

```text
scenario_sampling_failure
```

If history effects remain null, classify as:

```text
metric_artifact
```

Record the terminal-history null in prose, but keep manifest failure types on
the process-v2 taxonomy.

If reset/zero-current controls dominate, classify as:

```text
metric_artifact
```

## Required Artifacts

M1547 should write:

```text
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/accepted_calibrated_source_rows.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/measured_trace_rows.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/measured_snapshot_rows.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/measured_pair_candidates.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/accepted_pair_rows.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/intervention_rows.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/pair_summary.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/variant_summary.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/guardrail_summary.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/summary.json
```

No training corpus file should be written.

## Guardrails

```text
candidate_materialized: false
training_started: false
evaluation_started: false
replay_started: false
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
m1547-paper-route-calibrated-terminal-boundary-history-intervention-implementation
```
