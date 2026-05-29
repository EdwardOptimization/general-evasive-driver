# m1640-paper-route-contour-aware-exact-objective-projection-repair-implementation Research Review

## Summary

- Generated at UTC: 20260529T201325Z
- Type: objective_sanity
- Gate tier: infrastructure
- Promotion decision: contour_aware_projection_repair_negative_route_to_result_audit
- Decision reason: M1640 implements the no-checkpoint actor_mean projection probe but the pre-registered Adam lr=1e-3 recipe does not reduce positive exact residual; guardrails remain clean and audit is required

## Hypothesis

A bounded actor_mean-only projection can reduce exact residual from the controlled M1636 scale_1e-3 perturbation without writing a checkpoint or violating role guardrails.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1636_contour_aware_exact_objective_sensitivity_probe/summary.json, docs/m1638-paper-route-contour-aware-exact-objective-projection-repair-design.md, docs/m1639-paper-route-contour-aware-exact-objective-branch-synthesis.md
- parent_config: experiments/manifests/m1639-paper-route-contour-aware-exact-objective-branch-synthesis.json
- parent_objective: bounded no-checkpoint exact-objective projection repair probe
- derived_from: m1639-paper-route-contour-aware-exact-objective-branch-synthesis
- blocked_by: M1639 admits exactly one bounded no-checkpoint projection implementation and blocks PPO/promotion
- supersedes: direct checkpoint artifact after M1639, direct PPO after M1639, direct checkpoint promotion after M1639
- invalidates: None

## Success Criteria

- runs/m1640_contour_aware_exact_objective_projection_repair/summary.json exists
- initial_positive_exact_residual_mean > 1e-8
- repaired_positive_exact_residual_mean < initial_positive_exact_residual_mean
- positive_exact_residual_reduction_ratio >= 0.50
- repaired_actor_mean_l2_to_base <= initial_actor_mean_l2_to_base
- non_actor_mean_parameter_delta_max == 0.0
- repaired_checkpoint_written is false
- training_started ppo_used promoted private_holdout_used actor_input_contract_changed labels_enter_actor_input level3_self_id_claim_made are false

## Failure Criteria

- summary artifact is missing
- initial perturbation residual is not measurable
- projection fails to reduce exact residual
- non-actor_mean parameters change
- a repaired checkpoint file is written
- PPO promotion private holdout or actor-input changes are produced

## Evidence Gates

- M1640 must start from the controlled M1636 scale_1e-3 actor_mean perturbation
- M1640 must optimize only actor_mean.weight and actor_mean.bias in memory
- M1640 must reduce positive exact residual versus the perturbed candidate
- M1640 must write no checkpoint
- M1640 must not run PPO promotion private holdout or actor-input changes

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not write repaired checkpoint files
- do not run PPO
- do not run closed-loop training
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not treat diagnostics as positive targets
- do not treat donor_plus_hidden_action as a loss target
- do not claim level3 self-identification

## Failure Taxonomy

- training_instability

## Scoreboard

- milestone: m1640-paper-route-contour-aware-exact-objective-projection-repair-implementation
- type: objective_sanity
- checkpoint: runs/m1640_contour_aware_exact_objective_projection_repair/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contour_aware_projection_repair_negative_route_to_result_audit
- reason: M1640 implements the no-checkpoint actor_mean projection probe but the pre-registered Adam lr=1e-3 recipe does not reduce positive exact residual; guardrails remain clean and audit is required

## Next Blocker

m1641-paper-route-contour-aware-exact-objective-projection-repair-result-audit
