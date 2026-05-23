# m454-response-critical-ablation-corpus-export Research Review

## Summary

- Generated at UTC: 20260523T200203Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: moderate_response_critical_corpus_admit_m455
- Decision reason: M454 exports 685 accepted and 86 compact response-critical rows with balanced source coverage but mostly mixed dependency evidence

## Hypothesis

A structured response-critical exporter can turn M452 ablation rows into an interpretable corpus that separates current-response dependence from recurrent-history and action-history dependence.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m452_near_robust_ablation_seed9900/episodes.csv, runs/m452_late_robust_ablation_seed9900/episodes.csv, runs/m452_near_ablation_policy_difference_mining/policy_difference_candidates.csv, runs/m452_late_ablation_policy_difference_mining/policy_difference_candidates.csv
- parent_config: configs/m451_challenge_near_threshold_robust_zero_relvel.json, configs/m451_challenge_late_high_energy_robust_zero_relvel.json, experiments/manifests/m453-response-critical-ablation-corpus-design.json
- parent_objective: response-critical ablation corpus export
- derived_from: m453-response-critical-ablation-corpus-design
- blocked_by: m453-response-critical-ablation-corpus-design
- supersedes: None
- invalidates: None

## Success Criteria

- exporter writes candidates CSV compact CSV and summary JSON
- summary reports dependency-class counts
- summary reports failure-class counts
- documentation classifies the resulting corpus as strong moderate or weak evidence
- no checkpoint is promoted

## Failure Criteria

- exporter cannot read M452 episodes
- dependency and failure modes remain conflated
- actor contract changes
- corpus labels are treated as deployable actor inputs

## Evidence Gates

- implement response-critical ablation corpus exporter
- export candidates and compact corpus for M452 near and late runs
- summary separates dependency classes and failure classes
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not change actor input/output contract
- do not add hidden or oracle actor inputs
- do not use corpus labels as actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m454-response-critical-ablation-corpus-export
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: moderate_response_critical_corpus_admit_m455
- reason: M454 exports 685 accepted and 86 compact response-critical rows with balanced source coverage but mostly mixed dependency evidence

## Next Blocker

m455-response-critical-multiseed-expansion
