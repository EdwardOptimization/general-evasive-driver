# m1206-paper-route-corrected-profile-pilot-design Research Review

## Summary

- Generated at UTC: 20260528T060411Z
- Type: gate
- Gate tier: process
- Promotion decision: corrected_profile_pilot_design_admit_config_generation
- Decision reason: M1206 designs corrected public pilot with L0/L1/L2 normal/current-tiled controls and L3 online/corrected reset under fixed public seeds budgets eval rules and no promotion private holdout or self-ID claim

## Hypothesis

A corrected public pilot can be designed with current-tiled L2 controls and corrected L3 reset semantics under fixed budgets.

## Lineage

- parent_checkpoint: none
- parent_dataset: docs/m1205-paper-route-finite-window-gru-evidence-synthesis.md, runs/m1204_profile_control_repair_smoke/summary.json
- parent_config: experiments/manifests/m1205-paper-route-finite-window-gru-evidence-synthesis.json
- parent_objective: design corrected public pilot after branch synthesis
- derived_from: m1205-paper-route-finite-window-gru-evidence-synthesis
- blocked_by: synthesis continues the branch but requires corrected pilot design before any training
- supersedes: M1199-style comparison without current-tiled controls or corrected reset semantics
- invalidates: claiming finite-window history benefit without current-tiled capacity controls

## Success Criteria

- docs/m1206-paper-route-corrected-profile-pilot-design.md exists
- corrected profile set, seeds, budgets, eval rules, metrics, artifacts, and claim scope are fixed
- private holdout remains unused
- no training, PPO, candidate replay, promotion, private holdout, per-profile tuning, or actor-input contract expansion occurs
- next config-generation or pilot-run milestone is selected

## Failure Criteria

- M1206 trains or tunes profiles
- private holdout is used
- design omits current-tiled L2 controls or corrected reset semantics
- hidden or oracle actor inputs are introduced
- design claims performance evidence

## Evidence Gates

- M1206 may design the corrected public pilot only
- M1206 must not train controllers
- M1206 must not run PPO
- M1206 must not run candidate replay
- M1206 must not promote
- M1206 must not use private holdout
- M1206 must not tune profiles
- M1206 must not claim profile superiority or self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not use private holdout
- do not tune profiles
- do not promote
- do not claim performance evidence from design
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1206-paper-route-corrected-profile-pilot-design
- type: gate
- checkpoint: docs/m1206-paper-route-corrected-profile-pilot-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: corrected_profile_pilot_design_admit_config_generation
- reason: M1206 designs corrected public pilot with L0/L1/L2 normal/current-tiled controls and L3 online/corrected reset under fixed public seeds budgets eval rules and no promotion private holdout or self-ID claim

## Next Blocker

m1207-paper-route-corrected-profile-config-generation
