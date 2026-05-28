# m1250-paper-route-capability-separable-trajectory-proposal-source-smoke Research Review

## Summary

- Generated at UTC: 20260528T104849Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: trajectory_proposal_source_near_miss_route_to_result_audit
- Decision reason: M1250 proposal source smoke produced 425 proposals and a two-sided regret near-miss but accepted_separable_pairs remains 0

## Hypothesis

Condition-wise trajectory proposals can expose accepted capability-separable source rows that fixed shared lattices and local relocation missed.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1249-paper-route-capability-separable-trajectory-proposal-source-design.md, docs/m1248-paper-route-capability-separable-fine-relocation-negative-audit.md, runs/m1247_capability_separable_fine_relocation_calibration_smoke/summary.json
- parent_config: experiments/manifests/m1249-paper-route-capability-separable-trajectory-proposal-source-design.json, configs/m1236_extreme_fault_timing_repair_smoke.json
- parent_objective: run a bounded no-training condition-wise trajectory proposal source smoke
- derived_from: m1249-paper-route-capability-separable-trajectory-proposal-source-design
- blocked_by: M1248 finds fixed-lattice local relocation exhausted and M1249 selects trajectory proposal source mining
- supersedes: another local relocation-grid expansion before testing proposal source strength
- invalidates: None

## Success Criteria

- trajectory proposal source code exists
- focused tests exist
- runs/m1250_capability_separable_trajectory_proposal_source_smoke/summary.json exists
- trajectory_proposals > 0
- trajectory_proposal_rollouts > 0
- actor_parameters_changed == false
- training_started == false
- ppo_used == false
- promoted == false
- labels_enter_actor_input == false
- private holdout remains unused
- no actor-input contract expansion occurs

## Failure Criteria

- proposal source cannot produce trajectory proposals
- proposal source cannot produce rollouts
- actor parameters change
- proposal labels or oracle outcomes enter actor observations
- training or PPO starts
- promotion occurs

## Evidence Gates

- M1250 must preserve actor input contract
- M1250 must not train controllers
- M1250 must not run PPO
- M1250 must not use private holdout
- M1250 must not promote
- M1250 must keep proposal labels and oracle outcomes out of deployable actor inputs
- M1250 must report accepted separable pairs as diagnostic source evidence only

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters, proposal labels, oracle outcomes, or search outputs to actor inputs
- do not claim self-identification from source construction
- do not relax cross-regret thresholds after seeing the result

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1250-paper-route-capability-separable-trajectory-proposal-source-smoke
- type: infrastructure
- checkpoint: runs/m1250_capability_separable_trajectory_proposal_source_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: trajectory_proposal_source_near_miss_route_to_result_audit
- reason: M1250 proposal source smoke produced 425 proposals and a two-sided regret near-miss but accepted_separable_pairs remains 0

## Next Blocker

m1251-paper-route-capability-separable-trajectory-proposal-near-miss-audit
