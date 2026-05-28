# m1390-paper-route-causal-history-necessity-task-design Research Review

## Summary

- Generated at UTC: 20260528T225443Z
- Type: gate
- Gate tier: process
- Promotion decision: causal_history_necessity_task_design_admit_source_miner_implementation
- Decision reason: M1390 defines matched-current older-history warmup-latched tail-aligned and source-rich temporal task families with interventions source-diversity thresholds and source-miner next route

## Hypothesis

A causal history-necessity task/gate family can be designed to test history dependence directly after standard profile comparison fails to expose it.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1389-paper-route-history-profile-three-seed-public-pilot-result-audit.md, runs/m1388_history_profile_three_seed_public_pilot/summary.json, runs/m1379_promoted_base_source_rich_sequence_expanded_probe/summary.json
- parent_config: experiments/manifests/m1389-paper-route-history-profile-three-seed-public-pilot-result-audit.json
- parent_objective: design causal history-necessity task/gate family after fixed-budget profile pilot is negative for history necessity
- derived_from: m1389-paper-route-history-profile-three-seed-public-pilot-result-audit
- blocked_by: M1389 pivots away from blind profile scaling to causal history-necessity task design
- supersedes: running another profile repeat without a new history-necessity task, claiming recurrent belief from standard public profile pilot
- invalidates: None

## Success Criteria

- docs/m1390-paper-route-causal-history-necessity-task-design.md exists
- design specifies task families and interventions
- design specifies accepted-row and accepted-seed/source-diversity thresholds
- design chooses next mining or implementation route without training, PPO, promotion, private holdout, corpus export, or actor-input expansion

## Failure Criteria

- design document is missing
- design repeats standard profile comparison without making history causal
- design omits current-frame substitution controls
- design omits source-diversity thresholds
- design routes directly to training, PPO, promotion, private holdout, or corpus export without source design

## Evidence Gates

- M1390 must design history-necessity tasks before new mining/training
- M1390 must define matched-current or same-current intervention requirements
- M1390 must define accepted-seed/source-diversity thresholds
- M1390 must not train, run PPO, run new evaluation, promote, use private holdout, export corpus, or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run new evaluation
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not weaken claim standards after negative profile results
- do not claim level3 self-identification from design

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1390-paper-route-causal-history-necessity-task-design
- type: gate
- checkpoint: docs/m1390-paper-route-causal-history-necessity-task-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: causal_history_necessity_task_design_admit_source_miner_implementation
- reason: M1390 defines matched-current older-history warmup-latched tail-aligned and source-rich temporal task families with interventions source-diversity thresholds and source-miner next route

## Next Blocker

m1391-paper-route-causal-history-source-miner-implementation
