# m1282-paper-route-source-history-policy-gate-design Research Review

## Summary

- Generated at UTC: 20260528T133224Z
- Type: gate
- Gate tier: process
- Promotion decision: source_history_policy_gate_design_admit_no_training_implementation
- Decision reason: M1282 designs canonical 72-frame source-history projection action-likelihood metrics and admits no-training policy gate implementation

## Hypothesis

A no-training policy-side gate can be designed to test whether a recurrent actor is sensitive to M1280 correct-history versus wrong-history prefixes under the canonical 72-value human-view contract.

## Lineage

- parent_checkpoint: not_applicable_design_only
- parent_dataset: docs/m1281-paper-route-four-wheel-source-response-history-materialization-result-audit.md, runs/m1280_four_wheel_source_response_history_materialization/summary.json, runs/m1280_four_wheel_source_response_history_materialization/history_frame_rows.csv, runs/m1280_four_wheel_source_response_history_materialization/history_intervention_rows.csv, runs/m1280_four_wheel_source_response_history_materialization/wrong_history_pair_rows.csv, runs/m1277_four_wheel_source_intervention_materialization/intervention_observations.csv, runs/m1277_four_wheel_source_intervention_materialization/intervention_action_sequences.csv
- parent_config: experiments/manifests/m1281-paper-route-four-wheel-source-response-history-materialization-result-audit.json
- parent_objective: design a no-training policy-side gate for source histories
- derived_from: m1281-paper-route-four-wheel-source-response-history-materialization-result-audit
- blocked_by: M1281 admits policy-side gate design but policy-side projection and recurrent-history semantics are not yet specified
- supersedes: direct source-history policy evaluation without canonical frame projection design
- invalidates: None

## Success Criteria

- docs/m1282-paper-route-source-history-policy-gate-design.md exists
- design defines canonical projection from M1280 history rows to 72-value actor frames
- design defines normalization for response stream indices
- design defines correct-history wrong-history metrics
- design defines implementation artifacts and pass/fail conditions
- design blocks direct training and PPO
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design would append noncanonical history fields to actor observations
- design uses fault condition pair labels as actor inputs
- design treats action-level sensitivity as closed-loop self-identification proof
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1282 must preserve actor input contract
- M1282 must not train controllers
- M1282 must not run PPO
- M1282 must not use private holdout
- M1282 must not promote
- M1282 must define canonical 72-frame projection for M1280 history rows
- M1282 must define correct-history versus wrong-history policy-side metrics
- M1282 must keep fault condition and pair labels outside actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add branch/fault labels to actor-view frames
- do not append cmd_* as extra actor observation channels
- do not use per-wheel fault metadata as actor input
- do not treat policy-side action differences as closed-loop self-identification proof
- do not claim high-fidelity validation from the compact pilot

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1282-paper-route-source-history-policy-gate-design
- type: gate
- checkpoint: docs/m1282-paper-route-source-history-policy-gate-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_history_policy_gate_design_admit_no_training_implementation
- reason: M1282 designs canonical 72-frame source-history projection action-likelihood metrics and admits no-training policy gate implementation

## Next Blocker

m1283-paper-route-source-history-policy-gate-implementation
