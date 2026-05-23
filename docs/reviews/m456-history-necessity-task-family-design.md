# m456-history-necessity-task-family-design Research Review

## Summary

- Generated at UTC: 20260523T201714Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: admit_m457_history_necessity_config_implementation
- Decision reason: M456 designs late-reveal warm-up matched-current and wrong-history task layers to make recurrent history uniquely informative

## Hypothesis

Because M455 finds mostly mixed-dependency boundary rows, the next useful step is to design a task family that makes command-response history uniquely informative rather than continuing to mine the same challenge distribution.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m455_response_critical_multiseed_corpus/candidates.csv, runs/m455_response_critical_multiseed_corpus/compact_corpus.csv, runs/m455_response_critical_multiseed_corpus/summary.json
- parent_config: configs/m451_challenge_near_threshold_robust_zero_relvel.json, configs/m451_challenge_late_high_energy_robust_zero_relvel.json, experiments/manifests/m455-response-critical-multiseed-expansion.json
- parent_objective: history-necessity task-family design
- derived_from: m455-response-critical-multiseed-expansion
- blocked_by: m455-response-critical-multiseed-expansion
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies how to create recurrent-history necessity
- design includes reset-hidden wrong-history and no-action-history diagnostics
- design states pass and redirect criteria
- next implementation task is preregistered
- no checkpoint is promoted

## Failure Criteria

- design ignores M455's mixed-dependency finding
- design adds oracle actor inputs
- design jumps directly to training
- no implementation path is defined

## Evidence Gates

- design a task family that creates clearer recurrent-history necessity
- define matched-current or warm-up construction
- define wrong-history and reset-hidden diagnostics
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not change actor input/output contract
- do not add hidden or oracle actor inputs
- do not treat mixed-dependency M455 rows as self-ID proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m456-history-necessity-task-family-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m457_history_necessity_config_implementation
- reason: M456 designs late-reveal warm-up matched-current and wrong-history task layers to make recurrent history uniquely informative

## Next Blocker

m457-history-necessity-config-implementation
