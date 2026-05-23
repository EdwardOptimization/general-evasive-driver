# m453-response-critical-ablation-corpus-design Research Review

## Summary

- Generated at UTC: 20260523T195523Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: admit_m454_response_critical_ablation_corpus_export
- Decision reason: M453 designs dependency and failure-class taxonomy so M452 rows become interpretable corpus evidence instead of aggregate success claims

## Hypothesis

M452's weak aggregate ablation signal can still seed a useful response-critical corpus if the next mining pass separates current response, recurrent hidden state, action history, and failure mechanism.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m452_near_robust_ablation_seed9900/episodes.csv, runs/m452_late_robust_ablation_seed9900/episodes.csv, runs/m452_near_ablation_policy_difference_mining/policy_difference_candidates.csv, runs/m452_late_ablation_policy_difference_mining/policy_difference_candidates.csv
- parent_config: configs/m451_challenge_near_threshold_robust_zero_relvel.json, configs/m451_challenge_late_high_energy_robust_zero_relvel.json, experiments/manifests/m452-robust-challenge-response-ablation-benchmark.json
- parent_objective: response-critical ablation corpus design
- derived_from: m452-robust-challenge-response-ablation-benchmark
- blocked_by: m452-robust-challenge-response-ablation-benchmark
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies candidate selection criteria for response-critical rows
- design separates road-boundary failures from obstacle-collision margin failures
- design defines source-diverse compact corpus limits
- next implementation task is preregistered
- no checkpoint is promoted

## Failure Criteria

- design treats weak M452 aggregate deltas as promotion evidence
- failure modes are conflated
- actor contract changes
- no next implementation step is defined

## Evidence Gates

- separate current-response reset-hidden and action-history failure modes
- define source-diverse response-critical mining criteria
- define road-boundary versus obstacle-collision split
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not change actor input/output contract
- do not add hidden or oracle actor inputs
- do not tune checkpoint behavior from M452 ablation rows

## Failure Taxonomy

- none

## Scoreboard

- milestone: m453-response-critical-ablation-corpus-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m454_response_critical_ablation_corpus_export
- reason: M453 designs dependency and failure-class taxonomy so M452 rows become interpretable corpus evidence instead of aggregate success claims

## Next Blocker

m454-response-critical-ablation-corpus-export
