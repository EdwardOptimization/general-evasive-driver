# m1244-paper-route-capability-separable-short-sequence-lattice-smoke Research Review

## Summary

- Generated at UTC: 20260528T093355Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: short_sequence_lattice_smoke_infrastructure_pass_low_regret_route_to_source_window_audit
- Decision reason: M1244 infrastructure passes with 120 matched pairs 10320 sequence rollouts 9 fault-family pairs and 20 seeds but accepted_separable_pairs is 0 and result_class remains action_divergent_low_regret

## Hypothesis

A compact shared short-sequence lattice can expose hidden-dynamics action separability that the M1242 one-step lattice missed.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1243-paper-route-capability-separable-low-regret-audit.md, runs/m1242_capability_separable_source_constructor_smoke/summary.json
- parent_config: experiments/manifests/m1243-paper-route-capability-separable-low-regret-audit.json, configs/m1236_extreme_fault_timing_repair_smoke.json
- parent_objective: test whether short K-step action sequences expose hidden-dynamics action separability that one-step actions did not
- derived_from: m1243-paper-route-capability-separable-low-regret-audit
- blocked_by: M1242 produced action-divergent low-regret rows with zero accepted first-action separable pairs
- supersedes: more first-action threshold tuning on M1242 rows
- invalidates: None

## Success Criteria

- short-sequence source constructor code exists
- focused tests exist
- runs/m1244_capability_separable_short_sequence_lattice_smoke/summary.json exists
- matched_pair_count > 0
- sequence_rollouts > 0
- matched fault-family pairs >= 6
- matched seeds >= 6
- actor_parameters_changed == false
- training_started == false
- ppo_used == false
- promoted == false
- labels_enter_actor_input == false
- private holdout remains unused
- no actor-input contract expansion occurs

## Failure Criteria

- constructor cannot produce matched pairs
- constructor cannot produce sequence rollouts
- actor parameters change
- hidden labels enter actor observations
- training or PPO starts
- promotion occurs

## Evidence Gates

- M1244 must preserve actor input contract
- M1244 must not train controllers
- M1244 must not run PPO
- M1244 must not use private holdout
- M1244 must not promote
- M1244 must evaluate the same sequence candidates under both hidden-dynamics conditions
- M1244 must report accepted sequence-separable pairs as diagnostic only

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters or oracle labels to actor inputs
- do not claim self-identification from source construction
- do not lower M1242 thresholds and call that source-positive
- do not change simulator fidelity in the same milestone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1244-paper-route-capability-separable-short-sequence-lattice-smoke
- type: infrastructure
- checkpoint: runs/m1244_capability_separable_short_sequence_lattice_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: short_sequence_lattice_smoke_infrastructure_pass_low_regret_route_to_source_window_audit
- reason: M1244 infrastructure passes with 120 matched pairs 10320 sequence rollouts 9 fault-family pairs and 20 seeds but accepted_separable_pairs is 0 and result_class remains action_divergent_low_regret

## Next Blocker

m1245-paper-route-capability-separable-source-window-audit
