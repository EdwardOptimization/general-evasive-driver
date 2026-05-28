# m1259-paper-route-richer-fault-capability-source-smoke Research Review

## Summary

- Generated at UTC: 20260528T114211Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: richer_fault_capability_source_smoke_infrastructure_pass_source_negative_route_to_result_audit
- Decision reason: M1259 strict rerun fixes accepted-source semantics and produces 8 near-boundary viable pairs plus 4 action-divergent pairs but accepted_separable_pairs remains 0

## Hypothesis

Richer v4 proxy-fault source families can produce capability-separable matched-current rows where the narrower M1241-M1256 source family could not.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1258-paper-route-richer-fault-capability-source-design.md, docs/m1257-paper-route-capability-separable-source-construction-synthesis.md, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_config: experiments/manifests/m1258-paper-route-richer-fault-capability-source-design.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: run a bounded no-training capability-separable source smoke on richer v4 proxy-fault source family
- derived_from: m1258-paper-route-richer-fault-capability-source-design
- blocked_by: M1258 admits richer-fault/source-family smoke after M1257 closes local source construction
- supersedes: another local timing/proposal/relocation source tweak
- invalidates: None

## Success Criteria

- runs/m1259_richer_fault_capability_source_smoke/summary.json exists
- trajectory_proposals > 0
- trajectory_proposal_rollouts > 0
- matched_pair_count > 0
- unique_matched_fault_family_pairs is reported
- accepted_separable_pairs is reported
- min_cross_regret_margin remains 0.02
- actor_parameters_changed == false
- training_started == false
- ppo_used == false
- promoted == false
- labels_enter_actor_input == false
- private holdout remains unused
- no actor-input contract expansion occurs
- true high-fidelity/per-wheel physical claims remain blocked

## Failure Criteria

- run artifacts are missing
- proposal source cannot produce rollouts
- accepted thresholds are lowered
- actor parameters change
- fault labels or oracle outcomes enter actor observations
- training or PPO starts
- promotion occurs
- current single-track proxy faults are claimed as true physical per-wheel faults

## Evidence Gates

- M1259 must preserve actor input contract
- M1259 must not train controllers
- M1259 must not run PPO
- M1259 must not use private holdout
- M1259 must not promote
- M1259 must keep proxy fault labels and oracle outcomes out of deployable actor inputs
- M1259 must not lower accepted source thresholds
- M1259 must keep true high-fidelity/per-wheel physical claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters, fault labels, oracle outcomes, or search outputs to actor inputs
- do not lower min_cross_regret_margin
- do not accept negative own-branch margins
- do not claim current single-track proxies are true single-wheel or per-wheel faults
- do not claim self-identification from source construction

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m1259-paper-route-richer-fault-capability-source-smoke
- type: infrastructure
- checkpoint: runs/m1259_richer_fault_capability_source_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: richer_fault_capability_source_smoke_infrastructure_pass_source_negative_route_to_result_audit
- reason: M1259 strict rerun fixes accepted-source semantics and produces 8 near-boundary viable pairs plus 4 action-divergent pairs but accepted_separable_pairs remains 0

## Next Blocker

m1260-paper-route-richer-fault-capability-source-result-audit
