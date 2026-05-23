# m475-combined-adversarial-outcome-proof-probe Research Review

## Summary

- Generated at UTC: 20260523T215823Z
- Type: gate
- Gate tier: proof
- Promotion decision: combined_adversarial_outcome_probe_reject_proof_admit_m476
- Decision reason: M475 finds 197 near-boundary wrong-history rows but 0 proof rows; wrong history changes actions weakly but closed-loop outcomes remain no-effect

## Hypothesis

The M474 source-diverse adversarial pairs will contain near-boundary wrong-history interventions that produce closed-loop outcome degradation.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m474-combined-fresh-anchor-adversarial-search.json
- parent_objective: combined adversarial wrong-history outcome proof probe
- derived_from: m474-combined-fresh-anchor-adversarial-search
- blocked_by: m474-combined-fresh-anchor-adversarial-search
- supersedes: None
- invalidates: None

## Success Criteria

- action gate completes on M474 adversarial pairs
- outcome gate completes on M474 adversarial pairs
- outcome selector completes
- near-boundary proof_candidate_count >= 16
- proof_success_or_collision_or_completion_rows >= 4
- proof_probe_seed_count >= 6
- proof_obstacle_label_count >= 2
- proof_target_count >= 2
- proof_single_seed_share <= 0.50
- proof_single_label_share <= 0.70
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- action or outcome gate fails
- proof_candidate_count remains below 16
- only high-slack diagnostics are found
- proof rows are source-narrow
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- run action intervention gate on M474 adversarial pairs
- run continuation outcome gate on M474 adversarial pairs
- run outcome-critical selector and near-boundary wrong-history proof selector
- decide whether wrong-history outcome proof exists
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not relax near-boundary normal-margin ceiling
- do not count high-slack diagnostics as proof
- do not add privileged actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m475-combined-adversarial-outcome-proof-probe
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: combined_adversarial_outcome_probe_reject_proof_admit_m476
- reason: M475 finds 197 near-boundary wrong-history rows but 0 proof rows; wrong history changes actions weakly but closed-loop outcomes remain no-effect

## Next Blocker

m476-wrong-history-no-effect-mechanism-audit
