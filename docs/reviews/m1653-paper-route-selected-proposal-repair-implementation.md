# m1653-paper-route-selected-proposal-repair-implementation Research Review

## Summary

- Generated at UTC: 20260529T212007Z
- Type: objective_sanity
- Gate tier: infrastructure
- Promotion decision: selected_proposal_repair_negative_route_to_audit
- Decision reason: M1653 focused tests and guardrails pass but actor_mean-only selected-proposal repair fails the primary alpha 0.2 gate and only reduces alpha 1.0 by 7.26 percent so result audit is required

## Hypothesis

Actor_mean-only damped projection can reduce contour-aware exact residual on at least the smallest selected real same-line proposal delta without checkpoint artifacts.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt, runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_2.pt, runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_4.pt, runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_1_0.pt
- parent_dataset: docs/m1652-paper-route-selected-proposal-repair-design.md, runs/m1650_proposal_source_preflight/candidate_summary.csv, runs/m1630_contour_aware_full_target_materialization/summary.json
- parent_config: experiments/manifests/m1652-paper-route-selected-proposal-repair-design.json
- parent_objective: implement no-checkpoint selected-proposal actor_mean repair probe
- derived_from: m1652-paper-route-selected-proposal-repair-design
- blocked_by: M1652 admits exactly one no-checkpoint implementation before checkpoint artifact or replay gates
- supersedes: direct checkpoint artifact after M1652, direct replay gate after M1652, direct PPO after M1652, direct promotion after M1652
- invalidates: None

## Success Criteria

- runs/m1653_selected_proposal_repair/summary.json exists
- selected_candidate_count >= 2
- measurable_initial_residual_count == selected_candidate_count
- residual_reduced_count >= 1
- candidate_public_pass_count >= 1
- primary_alpha_0_2_pass == true
- checkpoint_artifact_count == 0
- base_interpolation_used_for_repair_count == 0
- non_actor_mean_parameter_changed_count == 0
- training_started_count ppo_used_count promoted_count private_holdout_used_count actor_input_contract_changed_count level3_self_id_claim_count are 0

## Failure Criteria

- summary artifact is missing
- selected proposal candidates differ from design without audit
- primary alpha 0.2 is not measurable or cannot be improved
- any checkpoint artifact is written
- base interpolation is used for repair
- diagnostics or donor-plus actions enter the loss target
- PPO promotion private holdout actor-input changes or level3 claims are produced

## Evidence Gates

- M1653 must run selected proposals alpha 0.2 and alpha 1.0, with alpha 0.4 optional if implemented as designed
- M1653 must initialize from proposal checkpoints and not base-interpolate repair
- M1653 must optimize actor_mean only
- M1653 must write metrics and no checkpoint artifacts
- M1653 must keep diagnostics zero-weight and donor-plus actions excluded from loss
- M1653 must route to result audit

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not write checkpoint artifacts
- do not base-interpolate repair candidates
- do not train
- do not run PPO
- do not run closed-loop evaluation
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not treat diagnostics as positive targets
- do not treat donor_plus_hidden_action as a loss target
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- training_instability

## Scoreboard

- milestone: m1653-paper-route-selected-proposal-repair-implementation
- type: objective_sanity
- checkpoint: runs/m1653_selected_proposal_repair/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: selected_proposal_repair_negative_route_to_audit
- reason: M1653 focused tests and guardrails pass but actor_mean-only selected-proposal repair fails the primary alpha 0.2 gate and only reduces alpha 1.0 by 7.26 percent so result audit is required

## Next Blocker

m1654-paper-route-selected-proposal-repair-result-audit
