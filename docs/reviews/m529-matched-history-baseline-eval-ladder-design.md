# m529-matched-history-baseline-eval-ladder-design Research Review

## Summary

- Generated at UTC: 20260524T024642Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: admit_m530_l0_baseline_smoke_repeat
- Decision reason: M529 pre-registers the staged matched-history baseline ladder and selects repeated L0 smoke before any performance comparison

## Hypothesis

A staged matched-history baseline evaluation ladder can be pre-registered so L0/L2/L3 smoke training and natural history-value evaluations remain comparable instead of becoming separately tuned runs.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m526_history_value_event_audit/summary.json, runs/m528_l0_current_observation_smoke
- parent_config: configs/ppo_m528_l0_current_observation_smoke.json, experiments/manifests/m528-matched-history-baseline-plumbing.json
- parent_objective: matched history baseline evaluation ladder
- derived_from: m528-matched-history-baseline-plumbing, m527-matched-history-baseline-design
- blocked_by: m528-matched-history-baseline-plumbing
- supersedes: None
- invalidates: None

## Success Criteria

- document baseline train/eval ordering
- define seed and budget matching rules
- define which artifacts must be retained for later paper-quality comparisons
- identify the next executable smoke milestone

## Failure Criteria

- design allows per-baseline tuning before comparison
- design treats M528 smoke performance as evidence
- design weakens the P0 input contract
- design uses private holdout results for repair without rotation

## Evidence Gates

- defined L0/L2/L3 matched smoke and evaluation ordering
- separated plumbing smoke from performance claims
- preserved P0 no-wheel no-privileged input contract
- reserved M526 natural event rows as public diagnostic surfaces only

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote checkpoint
- do not compare separately tuned baselines as matched evidence
- do not add privileged actor inputs
- do not use reset-hidden diagnostics as a trained baseline replacement

## Failure Taxonomy

- none

## Scoreboard

- milestone: m529-matched-history-baseline-eval-ladder-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m530_l0_baseline_smoke_repeat
- reason: M529 pre-registers the staged matched-history baseline ladder and selects repeated L0 smoke before any performance comparison

## Next Blocker

m530-l0-baseline-smoke-repeat
