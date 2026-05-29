# m1658-paper-route-fusion-actor-proposal-repair-design Research Review

## Summary

- Generated at UTC: 20260529T214350Z
- Type: gate
- Gate tier: process
- Promotion decision: fusion_actor_repair_design_route_to_branch_synthesis
- Decision reason: M1658 designs differentiable-feature fusion_actor no-checkpoint repair but routes to branch synthesis before any implementation checkpoint or replay route

## Hypothesis

A design-only fusion_actor repair route is the minimal justified next step after M1656 showed wider differentiable-feature scope signal.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt, runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_2.pt, runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_4.pt, runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_1_0.pt
- parent_dataset: docs/m1657-paper-route-selected-proposal-scope-sensitivity-result-audit.md, runs/m1656_selected_proposal_scope_sensitivity/summary.json, runs/m1656_selected_proposal_scope_sensitivity/scope_summary.csv, runs/m1656_selected_proposal_scope_sensitivity/guardrail_summary.csv
- parent_config: experiments/manifests/m1657-paper-route-selected-proposal-scope-sensitivity-result-audit.json
- parent_objective: design minimal differentiable-feature fusion_actor repair route after positive scope sensitivity
- derived_from: m1657-paper-route-selected-proposal-scope-sensitivity-result-audit
- blocked_by: M1657 admits design-only fusion_actor repair planning but blocks implementation checkpoint artifact and replay gate
- supersedes: direct fusion_actor repair implementation after M1657, direct checkpoint artifact after M1657, direct replay gate after M1657, direct PPO after M1657, direct promotion after M1657
- invalidates: None

## Success Criteria

- docs/m1658-paper-route-fusion-actor-proposal-repair-design.md exists
- design chooses fusion_actor and justifies not widening further
- design defines differentiable-feature no-checkpoint repair metrics and guardrails
- design defines primary alpha 0.2 and stress-candidate acceptance thresholds
- design explicitly routes next step
- checkpoint artifacts replay gates PPO training promotion private holdout actor-input changes and level3 claims remain blocked

## Failure Criteria

- design document is missing
- design runs projection repair training PPO or closed-loop evaluation
- design widens beyond fusion_actor without new evidence
- design routes directly to checkpoint artifact replay promotion private holdout actor-input changes or closed-loop evidence
- design claims paper-level or level3 self-identification evidence

## Evidence Gates

- M1658 must be design-only
- M1658 must choose fusion_actor as the minimal wider scope justified by M1656
- M1658 must define differentiable-feature no-checkpoint repair metrics and guardrails
- M1658 must define acceptance thresholds for primary alpha 0.2 and stress candidates
- M1658 must route to branch synthesis before implementation because cadence is reached
- M1658 must keep checkpoint artifacts replay gates PPO training promotion private holdout actor-input changes and level3 claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run repair
- do not run projection
- do not tune M1656 one-step factors
- do not run PPO
- do not train
- do not run closed-loop evaluation
- do not write checkpoint artifacts
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not treat diagnostics as positive targets
- do not treat donor_plus_hidden_action as a loss target
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1658-paper-route-fusion-actor-proposal-repair-design
- type: gate
- checkpoint: docs/m1658-paper-route-fusion-actor-proposal-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: fusion_actor_repair_design_route_to_branch_synthesis
- reason: M1658 designs differentiable-feature fusion_actor no-checkpoint repair but routes to branch synthesis before any implementation checkpoint or replay route

## Next Blocker

m1659-paper-route-proposal-projection-repair-branch-synthesis
