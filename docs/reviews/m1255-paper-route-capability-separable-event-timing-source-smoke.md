# m1255-paper-route-capability-separable-event-timing-source-smoke Research Review

## Summary

- Generated at UTC: 20260528T111711Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: event_timing_source_smoke_infrastructure_pass_source_negative_route_to_result_audit
- Decision reason: M1255 implements source timing overrides and runs bounded smoke with 424 proposals 848 rollouts 1 near-boundary viable pair and 2 action-divergent pairs but accepted_separable_pairs remains 0

## Hypothesis

Denser nearby source timing around the near-miss can produce accepted diagnostic capability-separable rows without threshold relaxation.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1254-paper-route-capability-separable-event-timing-source-design.md, docs/m1253-paper-route-capability-separable-trajectory-proposal-source-variable-audit.md, runs/m1252_capability_separable_proposal_margin_restoration_smoke/summary.json
- parent_config: experiments/manifests/m1254-paper-route-capability-separable-event-timing-source-design.json, configs/m1236_extreme_fault_timing_repair_smoke.json
- parent_objective: run a bounded no-training event-timing/source-state smoke around the trajectory proposal near-miss
- derived_from: m1254-paper-route-capability-separable-event-timing-source-design
- blocked_by: M1254 designs source timing overrides after M1253 identifies source_state_timing_near_miss
- supersedes: another proposal-budget expansion on the same source states
- invalidates: None

## Success Criteria

- event-timing source override code exists
- focused tests exist
- runs/m1255_capability_separable_event_timing_source_smoke/summary.json exists
- trajectory_proposals > 0
- trajectory_proposal_rollouts > 0
- effective source timing overrides are reported
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
- source timing overrides are not reported
- accepted thresholds are lowered
- actor parameters change
- timing/proposal labels or oracle outcomes enter actor observations
- training or PPO starts
- promotion occurs

## Evidence Gates

- M1255 must preserve actor input contract
- M1255 must not train controllers
- M1255 must not run PPO
- M1255 must not use private holdout
- M1255 must not promote
- M1255 must keep timing labels, proposal labels, and oracle outcomes out of deployable actor inputs
- M1255 must not lower accepted source thresholds

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters, timing labels, proposal labels, oracle outcomes, or search outputs to actor inputs
- do not lower min_cross_regret_margin
- do not accept negative own-branch margins
- do not claim self-identification from source construction

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1255-paper-route-capability-separable-event-timing-source-smoke
- type: infrastructure
- checkpoint: runs/m1255_capability_separable_event_timing_source_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: event_timing_source_smoke_infrastructure_pass_source_negative_route_to_result_audit
- reason: M1255 implements source timing overrides and runs bounded smoke with 424 proposals 848 rollouts 1 near-boundary viable pair and 2 action-divergent pairs but accepted_separable_pairs remains 0

## Next Blocker

m1256-paper-route-capability-separable-event-timing-source-result-audit
