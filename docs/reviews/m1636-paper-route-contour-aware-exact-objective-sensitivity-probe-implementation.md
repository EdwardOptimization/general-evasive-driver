# m1636-paper-route-contour-aware-exact-objective-sensitivity-probe-implementation Research Review

## Summary

- Generated at UTC: 20260529T195136Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: contour_aware_exact_objective_sensitivity_probe_public_pass_route_to_audit
- Decision reason: M1636 sensitivity probe keeps base residual zero detects actor_mean perturbation residual writes no checkpoints and routes to audit

## Hypothesis

Controlled in-memory perturbations of actor_mean parameters will produce measurable exact-objective residual while the base remains zero-residual.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1633_contour_aware_policy_target_exact_evaluator/summary.json, docs/m1635-paper-route-contour-aware-exact-objective-sensitivity-probe-design.md
- parent_config: experiments/manifests/m1635-paper-route-contour-aware-exact-objective-sensitivity-probe-design.json
- parent_objective: bounded in-memory sensitivity probe for contour-aware exact objective
- derived_from: m1635-paper-route-contour-aware-exact-objective-sensitivity-probe-design
- blocked_by: M1635 admits a sensitivity probe but blocks repair/update/training
- supersedes: direct objective-only repair from M1635, direct PPO after M1635, direct checkpoint promotion after M1635
- invalidates: None

## Success Criteria

- runs/m1636_contour_aware_exact_objective_sensitivity_probe/summary.json exists
- base_positive_exact_residual_mean == 0.0 or base_positive_policy_action_residual_l2_max <= 1e-6
- max_positive_exact_residual_mean_over_perturbations > 1e-8
- max_positive_policy_action_residual_l2_max_over_perturbations > 1e-5
- perturbed_checkpoint_written is false
- actor_update_run training_started ppo_used promoted private_holdout_used actor_input_contract_changed labels_enter_actor_input level3_self_id_claim_made are false

## Failure Criteria

- summary artifact is missing
- base residual is not near zero
- controlled perturbations produce no measurable positive residual
- perturbed checkpoints are written
- actor update training PPO promotion private holdout or actor-input changes are produced

## Evidence Gates

- M1636 must evaluate base and in-memory perturbed candidates
- M1636 must keep base residual near zero
- M1636 must show at least one perturbed candidate has measurable positive residual
- M1636 must not write perturbed checkpoints
- M1636 must not run actor update training PPO promotion or private holdout

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run gradient update
- do not train
- do not run PPO
- do not write perturbed checkpoints
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not treat diagnostics as positive targets
- do not treat donor_plus_hidden_action as a loss target
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1636-paper-route-contour-aware-exact-objective-sensitivity-probe-implementation
- type: infrastructure
- checkpoint: runs/m1636_contour_aware_exact_objective_sensitivity_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contour_aware_exact_objective_sensitivity_probe_public_pass_route_to_audit
- reason: M1636 sensitivity probe keeps base residual zero detects actor_mean perturbation residual writes no checkpoints and routes to audit

## Next Blocker

m1636-paper-route-contour-aware-exact-objective-sensitivity-probe-implementation
