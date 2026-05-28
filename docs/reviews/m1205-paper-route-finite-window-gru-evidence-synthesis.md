# m1205-paper-route-finite-window-gru-evidence-synthesis Research Review

## Summary

- Generated at UTC: 20260528T060113Z
- Type: gate
- Gate tier: process
- Promotion decision: continue_to_corrected_profile_pilot_design
- Decision reason: M1205 synthesizes M1195-M1204 evidence: infrastructure and public pilot trend are real but finite-window history and recurrent-belief claims remain blocked; branch continues to corrected pilot design with controls

## Hypothesis

The M1195-M1204 finite-window vs GRU evidence branch can be synthesized into a safe next-route decision.

## Lineage

- parent_checkpoint: none
- parent_dataset: docs/m1195-paper-route-train-entrypoint-profile-mask-integration.md, docs/m1199-paper-route-fair-comparison-pilot-run.md, docs/m1201-paper-route-profile-separability-audit.md, docs/m1204-paper-route-profile-control-repair-smoke-run.md
- parent_config: experiments/manifests/m1204-paper-route-profile-control-repair-smoke-run.json
- parent_objective: synthesize the paper-route finite-window vs GRU evidence branch before continuing
- derived_from: m1195-paper-route-train-entrypoint-profile-mask-integration, m1196-paper-route-profile-training-smoke-stage-a-run, m1197-paper-route-profile-training-smoke-stage-b-run, m1198-paper-route-fair-comparison-pilot-design, m1199-paper-route-fair-comparison-pilot-run, m1200-paper-route-fair-comparison-pilot-result-audit, m1201-paper-route-profile-separability-audit, m1202-paper-route-profile-control-repair-design, m1203-paper-route-profile-control-repair-implementation, m1204-paper-route-profile-control-repair-smoke-run
- blocked_by: workflow synthesis cadence fired after M1204
- supersedes: creating another narrow corrected pilot design without branch synthesis
- invalidates: continuing the profile-comparison branch without summarizing M1195-M1204 evidence and risks

## Success Criteria

- docs/m1205-paper-route-finite-window-gru-evidence-synthesis.md exists
- synthesis questions are answered
- private holdout remains unused
- no training, PPO, candidate replay, promotion, private holdout, per-profile tuning, or actor-input contract expansion occurs
- next branch decision is selected

## Failure Criteria

- M1205 trains or tunes profiles
- private holdout is used
- synthesis skips metric artifact or current-frame substitution risks
- hidden or oracle actor inputs are introduced
- synthesis makes paper-level or self-ID claims

## Evidence Gates

- M1205 may synthesize existing evidence only
- M1205 must not train controllers
- M1205 must not run PPO
- M1205 must not run candidate replay
- M1205 must not promote
- M1205 must not use private holdout
- M1205 must not tune profiles
- M1205 must not claim profile superiority or self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not use private holdout
- do not tune profiles
- do not promote
- do not claim paper-level evidence
- do not skip synthesis questions

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m1205-paper-route-finite-window-gru-evidence-synthesis
- type: gate
- checkpoint: docs/m1205-paper-route-finite-window-gru-evidence-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: continue_to_corrected_profile_pilot_design
- reason: M1205 synthesizes M1195-M1204 evidence: infrastructure and public pilot trend are real but finite-window history and recurrent-belief claims remain blocked; branch continues to corrected pilot design with controls

## Next Blocker

m1206-paper-route-corrected-profile-pilot-design
