# m1202-paper-route-profile-control-repair-design Research Review

## Summary

- Generated at UTC: 20260528T054922Z
- Type: gate
- Gate tier: process
- Promotion decision: profile_control_repair_design_admit_runtime_implementation
- Decision reason: M1202 designs corrected reset-hidden public eval semantics and current-tiled L2 capacity controls so the next comparison can separate history benefit from temporal-GRU capacity and reset-control metric artifacts

## Hypothesis

The next fair comparison can be made interpretable by designing reset-evaluation semantics and a capacity-matched current-tiled L2 control before more training.

## Lineage

- parent_checkpoint: runs/m1199_fair_comparison_pilot/profile_runs
- parent_dataset: runs/m1201_profile_separability_audit/summary.json, runs/m1201_profile_separability_audit/l2_older_history_action_sensitivity.csv, runs/m1201_profile_separability_audit/l3_hidden_action_sensitivity.csv, docs/m1201-paper-route-profile-separability-audit.md
- parent_config: experiments/manifests/m1201-paper-route-profile-separability-audit.json
- parent_objective: design diagnostic-control repairs before any longer profile comparison
- derived_from: m1201-paper-route-profile-separability-audit
- blocked_by: M1201 finds high current-frame substitution risk for L2 older history and a reset-control evaluation semantic artifact
- supersedes: directly repeating M1199 without corrected reset evaluation and capacity-matched current-tiled L2 controls
- invalidates: using M1199 L3_reset_control aggregate as a true reset-hidden diagnostic

## Success Criteria

- docs/m1202-paper-route-profile-control-repair-design.md exists
- reset_hidden_policy evaluation semantics are specified
- current-tiled L2 capacity control is specified
- focused tests and rerun protocol are specified
- private holdout remains unused
- no training, PPO, candidate replay, promotion, private holdout, per-profile tuning, or actor-input contract change occurs
- next implementation or synthesis milestone is selected

## Failure Criteria

- M1202 trains or tunes profiles
- private holdout is used
- M1202 treats repair design as performance evidence
- hidden or oracle actor inputs are introduced
- design fails to address either reset semantics or L2 capacity control

## Evidence Gates

- M1202 may design repairs only
- M1202 must not train controllers
- M1202 must not run PPO
- M1202 must not run candidate replay
- M1202 must not promote
- M1202 must not use private holdout
- M1202 must not tune profiles
- M1202 must not claim paper-level evidence or self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun the comparison before reset evaluation semantics are fixed
- do not claim finite-window history necessity without a current-tiled capacity control
- do not use private holdout
- do not tune one profile after M1199
- do not promote
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m1202-paper-route-profile-control-repair-design
- type: gate
- checkpoint: docs/m1202-paper-route-profile-control-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: profile_control_repair_design_admit_runtime_implementation
- reason: M1202 designs corrected reset-hidden public eval semantics and current-tiled L2 capacity controls so the next comparison can separate history benefit from temporal-GRU capacity and reset-control metric artifacts

## Next Blocker

m1203-paper-route-profile-control-repair-implementation
