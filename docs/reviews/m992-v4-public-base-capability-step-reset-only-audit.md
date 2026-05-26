# m992-v4-public-base-capability-step-reset-only-audit Research Review

## Summary

- Generated at UTC: 20260526T133215Z
- Type: gate
- Gate tier: process
- Promotion decision: route_to_sequence_level_action_response_mismatch_design
- Decision reason: M992 diagnoses wrong-history gaps near zero versus reset-hidden gaps large and routes to sequence-level intervention design

## Hypothesis

M991's reset-only result is a routeable intervention-design problem rather than evidence for immediate training: wrong-history hidden states are too compatible or too weak, while reset-hidden rows identify candidate sequence-intervention seeds.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m991-v4-public-base-capability-step-fault-source-wave.md, runs/m991_v4_public_base_capability_step_fault_source_wave/summary.json, runs/m991_v4_public_base_capability_step_fault_source_wave/reset_only_rows.csv, runs/m991_v4_public_base_capability_step_fault_source_wave/matched_cross_fault_pairs.csv
- parent_config: configs/m991_capability_step_fault_source_wave.json, experiments/manifests/m991-v4-public-base-capability-step-fault-source-wave.json
- parent_objective: audit why capability-step source wave is reset-only and choose the next no-training intervention route
- derived_from: m991-v4-public-base-capability-step-fault-source-wave, m990-v4-public-base-capability-step-fault-smoke
- blocked_by: M991 has 1380 reset-only rows but zero accepted wrong-history rows
- supersedes: None
- invalidates: counting M991 reset-only rows as wrong-history proof, training directly from M991 reset-only rows

## Success Criteria

- audit artifact exists
- M990 and M991 results are compared
- reset-only rows are separated from wrong-history accepted rows
- dominant fault-family pairs and seed coverage are summarized
- next route is explicitly chosen
- no training or PPO occurs

## Failure Criteria

- audit artifact is missing
- reset-only rows are treated as wrong-history proof
- route decision is missing
- training or PPO starts
- hidden event labels enter actor observations

## Evidence Gates

- M992 must not run PPO
- M992 must not promote
- M992 must not change actor inputs
- M992 must not count reset-only rows as wrong-history proof
- M992 must choose a route before further source mining or training

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add hidden event labels to actor observations
- do not train or optimize
- do not use private holdout
- do not claim true per-wheel/asymmetric faults
- do not export reset-only rows as accepted wrong-history rows
- do not proceed to PPO

## Failure Taxonomy

- none

## Scoreboard

- milestone: m992-v4-public-base-capability-step-reset-only-audit
- type: gate
- checkpoint: docs/m992-v4-public-base-capability-step-reset-only-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: route_to_sequence_level_action_response_mismatch_design
- reason: M992 diagnoses wrong-history gaps near zero versus reset-hidden gaps large and routes to sequence-level intervention design

## Next Blocker

m993-v4-public-base-capability-step-sequence-intervention-design
