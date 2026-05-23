# m477-persistent-wrong-history-intervention-design Research Review

## Summary

- Generated at UTC: 20260523T220544Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m478_persistent_wrong_history_intervention_implementation
- Decision reason: M477 designs diagnostic wrong_hold and wrong_late variants to test whether wrong belief persistence is the missing causal factor

## Hypothesis

A one-shot wrong-history injection is corrected too quickly; persistent or later wrong-history intervention will distinguish whether recurrent belief can be outcome-critical when the wrong belief is active during the emergency decision window.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m476_wrong_history_no_effect_mechanism_audit/summary.json, runs/m475_combined_adversarial_outcome_selector/candidates.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m476-wrong-history-no-effect-mechanism-audit.json
- parent_objective: persistent or later wrong-history intervention design
- derived_from: m476-wrong-history-no-effect-mechanism-audit
- blocked_by: m476-wrong-history-no-effect-mechanism-audit
- supersedes: None
- invalidates: None

## Success Criteria

- document the exact intervention variants to implement
- define how persistent wrong hidden state is applied without changing actor inputs
- define diagnostic pass criteria for action distance, trajectory distance, margin gap, success drop, and source diversity
- pre-register implementation artifacts for the next milestone
- no checkpoint is promoted

## Failure Criteria

- design confuses diagnostic intervention with deployable actor input
- design proposes training before intervention evidence
- design counts reset/zero-current degradation as wrong-history proof
- design relaxes normal-margin proof requirements

## Evidence Gates

- design a persistent wrong-history intervention that keeps the wrong hidden belief active for K emergency steps
- design a later-injection intervention at or after obstacle reveal
- define pass/fail criteria against M475 reset/zero-current and wrong-history baselines
- preserve P0 actor contract and no-privileged inputs
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not count artificial persistent intervention as deployable behavior proof without labeling it diagnostic
- do not relax near-boundary normal-margin requirements

## Failure Taxonomy

- none

## Scoreboard

- milestone: m477-persistent-wrong-history-intervention-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m478_persistent_wrong_history_intervention_implementation
- reason: M477 designs diagnostic wrong_hold and wrong_late variants to test whether wrong belief persistence is the missing causal factor

## Next Blocker

m478-persistent-wrong-history-intervention-implementation
