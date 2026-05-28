# m1271-paper-route-four-wheel-source-viability-calibration-smoke Research Review

## Summary

- Generated at UTC: 20260528T124221Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: four_wheel_source_viability_calibration_smoke_source_positive_route_to_result_audit
- Decision reason: M1271 calibrated no-policy source smoke produces 108 strict accepted rows across three fault families while preserving no-training no-PPO and actor-input guardrails

## Hypothesis

The calibrated four-wheel source grid can restore own-branch viability while preserving strict high-regret action divergence under unchanged source thresholds.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint
- parent_dataset: docs/m1270-paper-route-four-wheel-source-viability-calibration-design.md, runs/m1268_four_wheel_fault_source_shape_smoke/summary.json
- parent_config: experiments/manifests/m1270-paper-route-four-wheel-source-viability-calibration-design.json
- parent_objective: run bounded four-wheel source viability calibration smoke
- derived_from: m1270-paper-route-four-wheel-source-viability-calibration-design
- blocked_by: M1270 admits one bounded viability calibration smoke after M1268 collision dominance
- supersedes: another uncalibrated m1268_default source-shape rerun
- invalidates: None

## Success Criteria

- runs/m1271_four_wheel_source_viability_calibration_smoke/summary.json exists
- scenario_summary.csv exists
- snapshot_candidates.csv exists
- action_lattice.csv exists
- action_rollouts.csv exists
- matched_capability_pairs.csv exists
- accepted_separable_pairs.csv exists
- scenario_profile == viability_calibration
- collision-dominance diagnostics are reported
- actor_input_contract_changed == false
- labels_enter_actor_input == false
- training_started == false
- ppo_used == false
- promoted == false
- private_holdout_used == false
- accepted_thresholds_relaxed == false

## Failure Criteria

- run artifacts are missing
- scenario_profile is not viability_calibration
- observation mapping includes per-wheel/fault metadata
- accepted thresholds are lowered
- horizon-only rows are counted as success
- training or PPO starts
- promotion occurs
- high-fidelity validation is claimed

## Evidence Gates

- M1271 must preserve actor input contract
- M1271 must not train controllers
- M1271 must not run PPO
- M1271 must not use private holdout
- M1271 must not promote
- M1271 must use scenario_profile=viability_calibration
- M1271 must preserve strict accepted-source thresholds
- M1271 must preserve obstacle_completed or safe_stop success semantics
- M1271 must report accepted rows, collision dominance, and source diversity

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add per-wheel/fault labels to actor inputs
- do not lower accepted-source thresholds
- do not count horizon-only rows as success
- do not claim high-fidelity validation from the compact pilot
- do not use policy success as a substitute for strict source acceptance

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1271-paper-route-four-wheel-source-viability-calibration-smoke
- type: infrastructure
- checkpoint: runs/m1271_four_wheel_source_viability_calibration_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: four_wheel_source_viability_calibration_smoke_source_positive_route_to_result_audit
- reason: M1271 calibrated no-policy source smoke produces 108 strict accepted rows across three fault families while preserving no-training no-PPO and actor-input guardrails

## Next Blocker

m1272-paper-route-four-wheel-source-viability-calibration-result-audit
