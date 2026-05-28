# m1215-paper-route-causal-history-gate-design Research Review

## Summary

- Generated at UTC: 20260528T065440Z
- Type: gate
- Gate tier: process
- Promotion decision: causal_history_gate_design_admit_source_audit
- Decision reason: M1215 pre-registers a matched-current causal history gate with action and outcome stages reset delayed wrong-history zero-response zero-action and current-tiled controls plus failure taxonomy and routes next to source/tooling audit

## Hypothesis

A matched-current causal history gate can more directly test self-identification than aggregate profile comparison.

## Lineage

- parent_checkpoint: none
- parent_dataset: docs/m1214-paper-route-corrected-profile-evidence-synthesis.md, runs/m1209_corrected_profile_pilot/profile_aggregate.csv, runs/m1212_corrected_profile_repeat/profile_aggregate.csv
- parent_config: experiments/manifests/m1214-paper-route-corrected-profile-evidence-synthesis.json
- parent_objective: design a causal history gate after corrected profile comparisons fail to prove memory necessity
- derived_from: m1214-paper-route-corrected-profile-evidence-synthesis
- blocked_by: Profile comparisons cannot prove self-identification because current-tiled and reset controls explain key trends
- supersedes: running more broad profile pilots as the next default step
- invalidates: using aggregate profile ranking as memory-causality evidence

## Success Criteria

- docs/m1215-paper-route-causal-history-gate-design.md exists
- gate inputs and interventions are defined
- matched-current ambiguity requirements are defined
- success and failure thresholds are pre-registered
- private holdout remains unused
- no training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs
- next implementation or audit milestone is selected

## Failure Criteria

- M1215 trains or tunes profiles
- private holdout is used
- gate uses hidden or oracle actor inputs
- design lacks reset/delayed/wrong-history controls
- self-identification is claimed from profile aggregates

## Evidence Gates

- M1215 may design causal history gates only
- M1215 must target matched-current observations with different histories or hidden dynamics
- M1215 must pre-register normal reset delayed wrong-history and current-tiled controls
- M1215 must not train controllers
- M1215 must not run PPO
- M1215 must not use private holdout
- M1215 must not promote
- M1215 must not claim paper-level evidence or self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not use private holdout
- do not promote
- do not tune profiles
- do not use oracle actor inputs
- do not call aggregate ranking a causal history gate

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1215-paper-route-causal-history-gate-design
- type: gate
- checkpoint: docs/m1215-paper-route-causal-history-gate-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: causal_history_gate_design_admit_source_audit
- reason: M1215 pre-registers a matched-current causal history gate with action and outcome stages reset delayed wrong-history zero-response zero-action and current-tiled controls plus failure taxonomy and routes next to source/tooling audit

## Next Blocker

m1216-paper-route-causal-history-source-audit
