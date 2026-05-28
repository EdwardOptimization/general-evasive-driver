# m1242-paper-route-capability-separable-source-constructor-smoke Research Review

## Summary

- Generated at UTC: 20260528T091939Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: capability_separable_constructor_smoke_infrastructure_pass_low_regret_route_to_audit
- Decision reason: M1242 infrastructure passes with 160 matched pairs 24000 action rollouts 10 fault-family pairs and 20 seeds but accepted_separable_pairs is 0 and result_class is action_divergent_low_regret

## Hypothesis

A small local shared-base first-action lattice can determine whether current matched hidden-dynamics sources contain action-separable cases before actor history tests.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1241-paper-route-capability-separable-source-construction-design.md
- parent_config: experiments/manifests/m1241-paper-route-capability-separable-source-construction-design.json, configs/m1236_extreme_fault_timing_repair_smoke.json
- parent_objective: implement and run bounded action-lattice source-construction smoke to test hidden-dynamics action separability
- derived_from: m1241-paper-route-capability-separable-source-construction-design
- blocked_by: M1241 admits only bounded no-training source construction before actor self-ID tests
- supersedes: testing actor history before proving source action separability
- invalidates: None

## Success Criteria

- src/autodrift/capability_separable_source_constructor.py exists
- tests/test_capability_separable_source_constructor.py exists
- runs/m1242_capability_separable_source_constructor_smoke/summary.json exists
- each matched pair evaluates the same clipped action candidates under both hidden-dynamics conditions
- matched_pair_count > 0
- action_rollouts > 0
- matched fault-family pairs >= 6
- matched seeds >= 6
- model_fidelity_limits.md exists
- actor_parameters_changed == false
- training_started == false
- ppo_used == false
- promoted == false
- labels_enter_actor_input == false
- private holdout remains unused
- no actor-input contract expansion occurs

## Failure Criteria

- constructor cannot produce matched pairs
- constructor cannot produce action rollouts
- actor parameters change
- hidden labels enter actor observations
- model fidelity boundary is missing
- training or PPO starts
- promotion occurs

## Evidence Gates

- M1242 must preserve actor input contract
- M1242 must not train controllers
- M1242 must not run PPO
- M1242 must not use private holdout
- M1242 must not promote
- M1242 must keep hidden dynamics and oracle/source labels out of deployable actor inputs
- M1242 must report accepted separable pairs as diagnostic only

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters or oracle labels to actor inputs
- do not claim self-identification from source construction
- do not treat the action lattice as a deployable controller

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1242-paper-route-capability-separable-source-constructor-smoke
- type: infrastructure
- checkpoint: runs/m1242_capability_separable_source_constructor_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: capability_separable_constructor_smoke_infrastructure_pass_low_regret_route_to_audit
- reason: M1242 infrastructure passes with 160 matched pairs 24000 action rollouts 10 fault-family pairs and 20 seeds but accepted_separable_pairs is 0 and result_class is action_divergent_low_regret

## Next Blocker

m1243-paper-route-capability-separable-low-regret-audit
