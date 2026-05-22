# m283-current-family-rejected-trajectory-anchor-export Research Review

## Summary

- Generated at UTC: 20260522T185807Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_rejected_trajectory_anchored_update
- Decision reason: M283 exports 669 current-family rejected-history trajectory rows and a 12594-row combined recovery/rejected anchor with all M267/M264 rows included

## Hypothesis

A current-base rejected-history trajectory anchor can preserve the closed-loop wrong-history branch that one-step rejected action anchoring failed to retain.

## Lineage

- parent_checkpoint: runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
- parent_dataset: runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, runs/m279_combined_retention_recovery_anchor/combined_trajectory_anchor.npz
- parent_config: experiments/manifests/m282-current-family-rejected-trajectory-anchor-design.json, docs/m282-current-family-rejected-trajectory-anchor-design.md
- parent_objective: export current-family rejected-history trajectory retention anchors
- derived_from: m282-current-family-rejected-trajectory-anchor-design
- blocked_by: m282-current-family-rejected-trajectory-anchor-design
- supersedes: None
- invalidates: None

## Success Criteria

- reconstruct M272 M267/M264 wrong-history rollouts with current M272 hidden states
- export rejected_trajectory_anchor.npz
- export combined_recovery_rejected_anchor.npz
- validate exported NPZ shapes through the existing trajectory anchor loader
- no PPO or actor update is run

## Failure Criteria

- failed M267/M264 rows are missing
- source checkpoint hidden states are used as current actor input
- exported anchors do not load
- PPO or actor update is run

## Evidence Gates

- export rejected_trajectory_anchor.npz for M267/M264 wrong-history rollouts
- include all 17 M267/M264 rows and force failed rows 4 6 11 13 15 16
- export combined_recovery_rejected_anchor.npz with M279 combined anchor plus rejected rows
- validate NPZ files through load_trajectory_action_anchor
- do not run PPO or actor update

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M283
- do not run a new actor update in M283
- do not use old checkpoint hidden states
- do not change actor inputs
- do not skip M267/M264 failed rows

## Failure Taxonomy

- none

## Scoreboard

- milestone: m283-current-family-rejected-trajectory-anchor-export
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_rejected_trajectory_anchored_update
- reason: M283 exports 669 current-family rejected-history trajectory rows and a 12594-row combined recovery/rejected anchor with all M267/M264 rows included

## Next Blocker

m284-rejected-trajectory-anchored-update
