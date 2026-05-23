# m478-persistent-wrong-history-intervention-implementation Research Review

## Summary

- Generated at UTC: 20260523T221222Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: persistent_wrong_history_diagnostic_pass_admit_m479
- Decision reason: M478 implements the diagnostic gate and finds wrong_hold_16 gives 25 proof-style rows while wrong_once remains 0

## Hypothesis

If fast recurrent correction is the M475 blocker, then holding or late-injecting the wrong hidden state during the emergency window will create larger trajectory and terminal-margin degradation than one-shot wrong history.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv, runs/m476_wrong_history_no_effect_mechanism_audit/summary.json
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m477-persistent-wrong-history-intervention-design.json
- parent_objective: persistent wrong-history diagnostic intervention implementation
- derived_from: m477-persistent-wrong-history-intervention-design
- blocked_by: m477-persistent-wrong-history-intervention-design
- supersedes: None
- invalidates: None

## Success Criteria

- new diagnostic module and tests are added
- smoke run completes on M474 adversarial pairs
- wrong_once reproduces M475 no-effect baseline
- at least one persistent/later variant reports whether proof-style degradation appears
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- implementation changes deployable actor inputs
- persistent variant semantics are ambiguous or untested
- smoke run cannot reconstruct snapshots
- training or checkpoint promotion is performed

## Evidence Gates

- implement persistent_wrong_history_intervention_gate
- add focused tests for wrong_hold and wrong_late variant semantics
- run a no-training smoke on M474 adversarial pairs
- report whether persistent/later wrong-hidden variants create source-diverse outcome degradation
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not count artificial persistent intervention as deployable behavior proof
- do not relax near-boundary normal-margin requirements

## Failure Taxonomy

- none

## Scoreboard

- milestone: m478-persistent-wrong-history-intervention-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: persistent_wrong_history_diagnostic_pass_admit_m479
- reason: M478 implements the diagnostic gate and finds wrong_hold_16 gives 25 proof-style rows while wrong_once remains 0

## Next Blocker

m479-natural-late-wrong-history-proof-path-design
