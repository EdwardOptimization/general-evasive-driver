# m1204-paper-route-profile-control-repair-smoke-run Research Review

## Summary

- Generated at UTC: 20260528T055829Z
- Type: gate
- Gate tier: infrastructure
- Promotion decision: profile_control_repair_smoke_pass_route_to_corrected_pilot_design
- Decision reason: M1204 no-training runtime smoke passes: current-tiled L2 works in single and sync vector env reset/step paths raw observations are not tiled and evaluation reset policy honors every-step control

## Hypothesis

Corrected reset and current-tiled controls work in no-training runtime/eval paths.

## Lineage

- parent_checkpoint: none
- parent_dataset: docs/m1203-paper-route-profile-control-repair-implementation.md, tests/test_controller_profile_runtime.py, tests/test_evaluate_reset_hidden_policy.py
- parent_config: experiments/manifests/m1203-paper-route-profile-control-repair-implementation.json
- parent_objective: smoke test corrected reset and current-tiled runtime controls before training
- derived_from: m1203-paper-route-profile-control-repair-implementation
- blocked_by: M1203 implements corrected control plumbing but no runtime smoke artifact has been written
- supersedes: assuming focused unit tests are enough before corrected pilot rerun
- invalidates: running corrected PPO pilot without a no-training runtime smoke

## Success Criteria

- docs/m1204-paper-route-profile-control-repair-smoke-run.md exists
- runs/m1204_profile_control_repair_smoke/summary.json exists
- current-tiled runtime smoke passes
- reset-policy eval smoke passes
- private holdout remains unused
- no training, PPO, candidate replay, promotion, private holdout, per-profile tuning, or actor-input contract expansion occurs
- next corrected pilot or repair milestone is selected

## Failure Criteria

- M1204 trains or tunes profiles
- private holdout is used
- smoke treats runtime checks as performance evidence
- hidden or oracle actor inputs are introduced
- failed smoke is ignored

## Evidence Gates

- M1204 may run no-training runtime smoke only
- M1204 must not train controllers
- M1204 must not run PPO
- M1204 must not run candidate replay
- M1204 must not promote
- M1204 must not use private holdout
- M1204 must not tune profiles
- M1204 must not claim profile superiority or self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not use private holdout
- do not tune profiles
- do not promote
- do not claim performance evidence
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1204-paper-route-profile-control-repair-smoke-run
- type: gate
- checkpoint: runs/m1204_profile_control_repair_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: profile_control_repair_smoke_pass_route_to_corrected_pilot_design
- reason: M1204 no-training runtime smoke passes: current-tiled L2 works in single and sync vector env reset/step paths raw observations are not tiled and evaluation reset policy honors every-step control

## Next Blocker

m1205-paper-route-finite-window-gru-evidence-synthesis
