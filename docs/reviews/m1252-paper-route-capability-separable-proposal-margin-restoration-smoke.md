# m1252-paper-route-capability-separable-proposal-margin-restoration-smoke Research Review

## Summary

- Generated at UTC: 20260528T105808Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: proposal_margin_restoration_near_miss_persists_route_to_source_variable_audit
- Decision reason: M1252 targeted repair improves pair 5 near-miss to -0.000661 margin but accepted_separable_pairs remains 0

## Hypothesis

A positive near-zero viability-band target with slightly richer trajectory proposals can turn M1250's near-miss into accepted diagnostic source rows without threshold relaxation.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1251-paper-route-capability-separable-trajectory-proposal-near-miss-audit.md, runs/m1250_capability_separable_trajectory_proposal_source_smoke/summary.json, runs/m1250_capability_separable_trajectory_proposal_source_smoke/matched_capability_pairs.csv
- parent_config: experiments/manifests/m1251-paper-route-capability-separable-trajectory-proposal-near-miss-audit.json, configs/m1236_extreme_fault_timing_repair_smoke.json
- parent_objective: run one targeted no-training margin-restoration source smoke for M1250 trajectory proposal near-miss
- derived_from: m1251-paper-route-capability-separable-trajectory-proposal-near-miss-audit
- blocked_by: M1251 finds M1250 pair 5 is a two-sided regret near-miss with slightly negative own-branch margins
- supersedes: lowering source-positive thresholds, starting training on zero accepted source rows
- invalidates: None

## Success Criteria

- runs/m1252_capability_separable_proposal_margin_restoration_smoke/summary.json exists
- trajectory_proposals > 0
- trajectory_proposal_rollouts > 0
- accepted_separable_pairs is reported
- min_cross_regret_margin remains 0.02
- actor_parameters_changed == false
- training_started == false
- ppo_used == false
- promoted == false
- labels_enter_actor_input == false
- private holdout remains unused
- no actor-input contract expansion occurs

## Failure Criteria

- run artifacts are missing
- proposal source cannot produce rollouts
- accepted thresholds are lowered
- actor parameters change
- proposal labels or oracle outcomes enter actor observations
- training or PPO starts
- promotion occurs

## Evidence Gates

- M1252 must preserve actor input contract
- M1252 must not train controllers
- M1252 must not run PPO
- M1252 must not use private holdout
- M1252 must not promote
- M1252 must keep proposal labels and oracle outcomes out of deployable actor inputs
- M1252 must not lower accepted source thresholds

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters, proposal labels, oracle outcomes, or search outputs to actor inputs
- do not lower min_cross_regret_margin
- do not accept negative own-branch margins
- do not claim self-identification from source construction

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1252-paper-route-capability-separable-proposal-margin-restoration-smoke
- type: infrastructure
- checkpoint: runs/m1252_capability_separable_proposal_margin_restoration_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: proposal_margin_restoration_near_miss_persists_route_to_source_variable_audit
- reason: M1252 targeted repair improves pair 5 near-miss to -0.000661 margin but accepted_separable_pairs remains 0

## Next Blocker

m1253-paper-route-capability-separable-trajectory-proposal-source-variable-audit
