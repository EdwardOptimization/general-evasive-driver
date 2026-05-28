# m1247-paper-route-capability-separable-fine-relocation-calibration-smoke Research Review

## Summary

- Generated at UTC: 20260528T103320Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: fine_relocation_valid_source_negative_route_to_limit_audit
- Decision reason: M1247 focused fine relocation smoke produced 96 fine candidates and one near-boundary viable selected pair but accepted_separable_pairs remains 0

## Hypothesis

Fine relocation around M1246 near-positive rows can produce at least diagnostic accepted capability-separable source rows without changing actor inputs or training.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1246-paper-route-capability-separable-viability-band-relocation-smoke.md, runs/m1246_capability_separable_viability_band_relocation_smoke/summary.json, runs/m1246_capability_separable_viability_band_relocation_smoke/relocation_candidates.csv
- parent_config: experiments/manifests/m1246-paper-route-capability-separable-viability-band-relocation-smoke.json
- parent_objective: fine-calibrate relocation around near-positive source rows that have strong cross-regret but slightly negative best margins
- derived_from: m1246-paper-route-capability-separable-viability-band-relocation-smoke
- blocked_by: M1246 produced near-boundary rows and one two-sided cross-regret row, but accepted_separable_pairs remained zero because the best margins were slightly negative
- supersedes: training on coarse relocated source rows, jumping directly to simulator-fidelity redesign before fine relocation calibration
- invalidates: None

## Success Criteria

- fine relocation calibration code exists
- focused tests exist
- runs/m1247_capability_separable_fine_relocation_calibration_smoke/summary.json exists
- fine relocation candidates > 0
- sequence_rollouts > 0
- actor_parameters_changed == false
- training_started == false
- ppo_used == false
- promoted == false
- labels_enter_actor_input == false
- private holdout remains unused
- no actor-input contract expansion occurs

## Failure Criteria

- constructor cannot produce fine relocation candidates
- constructor cannot produce sequence rollouts
- actor parameters change
- hidden or relocation labels enter actor observations
- training or PPO starts
- promotion occurs

## Evidence Gates

- M1247 must preserve actor input contract
- M1247 must not train controllers
- M1247 must not run PPO
- M1247 must not use private holdout
- M1247 must not promote
- M1247 must keep relocation labels and oracle outcomes out of deployable actor inputs
- M1247 must report accepted separable pairs as diagnostic only

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters, relocation labels, or oracle outcomes to actor inputs
- do not claim self-identification from source construction
- do not lower the source-positive cross-regret threshold

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1247-paper-route-capability-separable-fine-relocation-calibration-smoke
- type: infrastructure
- checkpoint: runs/m1247_capability_separable_fine_relocation_calibration_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: fine_relocation_valid_source_negative_route_to_limit_audit
- reason: M1247 focused fine relocation smoke produced 96 fine candidates and one near-boundary viable selected pair but accepted_separable_pairs remains 0

## Next Blocker

m1248-paper-route-capability-separable-fine-relocation-negative-audit
