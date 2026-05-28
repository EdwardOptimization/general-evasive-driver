# m1291-paper-route-source-history-directional-repair-design Research Review

## Summary

- Generated at UTC: 20260528T142339Z
- Type: gate
- Gate tier: process
- Promotion decision: source_history_directional_repair_design_admit_actor_mean_feasibility_probe
- Decision reason: M1291 rejects blind scalar-loss continuation and admits a no-PPO actor_mean directional feasibility probe before scope escalation or PPO

## Hypothesis

A no-PPO directional repair path can be designed to address the M1290 magnitude-compression failure mode without actor-input expansion.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m1288_source_history_objective_only_update/checkpoints/raw_objective_update.pt
- parent_dataset: docs/m1290-paper-route-source-history-directional-conflict-audit.md, runs/m1290_source_history_directional_conflict_audit/summary.json, runs/m1290_source_history_directional_conflict_audit/directional_conflict_rows.csv
- parent_config: experiments/manifests/m1290-paper-route-source-history-directional-conflict-audit.json
- parent_objective: design no-PPO directional repair after M1290 classifies M1288 as magnitude compression
- derived_from: m1290-paper-route-source-history-directional-conflict-audit
- blocked_by: M1290 shows exact-loss improvement with after_mutually_exclusive_fraction=1.0
- supersedes: blindly continuing actor_mean scalar-loss updates
- invalidates: None

## Success Criteria

- docs/m1291-paper-route-source-history-directional-repair-design.md exists
- design directly references M1290 mutually-exclusive sign rows
- design compares repair options
- design selects a bounded next implementation or routes to corpus repair
- design specifies row-wise directional pass/fail gates
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design ignores M1290 magnitude-compression result
- design starts PPO directly
- design adds actor inputs
- design overclaims self-identification
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1291 must preserve actor input contract
- M1291 must not train
- M1291 must not run PPO
- M1291 must not use private holdout
- M1291 must not promote
- M1291 must design a directional repair path that directly addresses mutually-exclusive sign rows
- M1291 must specify whether implementation should use actor_mean continuation, pair-group objective, trainable-scope escalation, or corpus repair

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not treat scalar loss improvement as row-wise directional repair
- do not overclaim self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1291-paper-route-source-history-directional-repair-design
- type: gate
- checkpoint: docs/m1291-paper-route-source-history-directional-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_history_directional_repair_design_admit_actor_mean_feasibility_probe
- reason: M1291 rejects blind scalar-loss continuation and admits a no-PPO actor_mean directional feasibility probe before scope escalation or PPO

## Next Blocker

m1292-paper-route-source-history-actor-mean-directional-feasibility-probe
