# m1284-paper-route-source-history-objective-design Research Review

## Summary

- Generated at UTC: 20260528T134426Z
- Type: gate
- Gate tier: process
- Promotion decision: source_history_objective_design_admit_exact_evaluator
- Decision reason: M1284 designs exact no-PPO source-history preference objective and admits full-corpus no-update evaluator before branch synthesis

## Hypothesis

An exact no-PPO source-history preference objective can be designed to address M1283's weak directional action-level signal without expanding actor inputs or starting PPO.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1283-paper-route-source-history-policy-gate-implementation.md, runs/m1283_source_history_policy_gate/summary.json, runs/m1283_source_history_policy_gate/policy_gate_rows.csv, runs/m1283_source_history_policy_gate/history_projection_audit.csv
- parent_config: experiments/manifests/m1283-paper-route-source-history-policy-gate-implementation.json
- parent_objective: design exact no-PPO source-history preference objective after weak policy-side gate signal
- derived_from: m1283-paper-route-source-history-policy-gate-implementation
- blocked_by: M1283 implemented the gate but the current checkpoint has weak directional source-history signal
- supersedes: starting PPO from weak source-history action-level signal
- invalidates: None

## Success Criteria

- docs/m1284-paper-route-source-history-objective-design.md exists
- design defines correct-history and wrong-history preference loss terms
- design defines exact full-corpus evaluator metrics
- design defines retention and branch-cadence guardrails
- design admits at most a no-PPO objective implementation
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design ignores M1283 weak signal
- design starts PPO directly
- design uses labels as actor inputs
- design overclaims self-identification
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1284 must preserve actor input contract
- M1284 must not train controllers
- M1284 must not run PPO
- M1284 must not use private holdout
- M1284 must not promote
- M1284 must design an exact source-history preference objective
- M1284 must keep M1283 weak-signal result as negative evidence
- M1284 must define no-PPO objective-only implementation criteria

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not treat M1283 weak signal as PPO admission
- do not add fault condition pair or probe labels to actor inputs
- do not claim self-identification from objective design
- do not claim high-fidelity validation from the compact pilot

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1284-paper-route-source-history-objective-design
- type: gate
- checkpoint: docs/m1284-paper-route-source-history-objective-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_history_objective_design_admit_exact_evaluator
- reason: M1284 designs exact no-PPO source-history preference objective and admits full-corpus no-update evaluator before branch synthesis

## Next Blocker

m1285-paper-route-source-history-objective-evaluator
