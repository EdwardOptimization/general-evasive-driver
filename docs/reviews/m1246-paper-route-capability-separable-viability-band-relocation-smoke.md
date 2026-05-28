# m1246-paper-route-capability-separable-viability-band-relocation-smoke Research Review

## Summary

- Generated at UTC: 20260528T101236Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: viability_band_relocation_infrastructure_pass_near_positive_route_to_fine_relocation
- Decision reason: M1246 infrastructure passes with 48 relocated pairs 24 near-boundary viability pairs and one near-positive two-sided cross-regret row but accepted_separable_pairs remains 0

## Hypothesis

Relocating matched source geometry into a near-boundary viability band can expose hidden-dynamics action separability that broad matched windows missed.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1245-paper-route-capability-separable-source-window-audit.md, runs/m1244_capability_separable_short_sequence_lattice_smoke/summary.json
- parent_config: experiments/manifests/m1245-paper-route-capability-separable-source-window-audit.json, configs/m1236_extreme_fault_timing_repair_smoke.json
- parent_objective: relocate matched source geometry into a near-boundary viability band before action-separability testing
- derived_from: m1245-paper-route-capability-separable-source-window-audit
- blocked_by: M1245 finds broad matched windows are bifurcated into nonviable or easy states with no near-boundary viability band
- supersedes: more sequence-template tuning before source-window repair
- invalidates: None

## Success Criteria

- relocation source constructor code exists
- focused tests exist
- runs/m1246_capability_separable_viability_band_relocation_smoke/summary.json exists
- relocated matched pairs > 0
- sequence_rollouts > 0
- near_boundary_viability_pairs is reported
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

- constructor cannot produce relocated matched pairs
- constructor cannot produce sequence rollouts
- actor parameters change
- hidden or relocation labels enter actor observations
- training or PPO starts
- promotion occurs

## Evidence Gates

- M1246 must preserve actor input contract
- M1246 must not train controllers
- M1246 must not run PPO
- M1246 must not use private holdout
- M1246 must not promote
- M1246 must keep relocation labels and oracle outcomes out of deployable actor inputs
- M1246 must report accepted separable pairs as diagnostic only

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters, relocation labels, or oracle outcomes to actor inputs
- do not claim self-identification from source construction
- do not change simulator fidelity in the same milestone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1246-paper-route-capability-separable-viability-band-relocation-smoke
- type: infrastructure
- checkpoint: runs/m1246_capability_separable_viability_band_relocation_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: viability_band_relocation_infrastructure_pass_near_positive_route_to_fine_relocation
- reason: M1246 infrastructure passes with 48 relocated pairs 24 near-boundary viability pairs and one near-positive two-sided cross-regret row but accepted_separable_pairs remains 0

## Next Blocker

m1247-paper-route-capability-separable-fine-relocation-calibration-smoke
