# m282-current-family-rejected-trajectory-anchor-design Research Review

## Summary

- Generated at UTC: 20260522T185247Z
- Type: gate
- Gate tier: proof
- Promotion decision: implement_current_family_rejected_trajectory_anchor_export
- Decision reason: M282 designs trajectory-level M267/M264 wrong-history retention because one-step rejected-hidden anchoring does not preserve closed-loop success-drop proof

## Hypothesis

Current-family wrong-history retention needs a trajectory-level rejected-history anchor because one-step rejected action anchoring does not preserve closed-loop wrong-history failure.

## Lineage

- parent_checkpoint: runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt, runs/m281_m272_actor_coupling_m270_rejected_hidden_recovery_anchor_s10_lr5e5_seed10077/optimized_checkpoint.pt
- parent_dataset: runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, runs/m281_m267_m264_replay_gate_seed10070/boundary_replay_rows.csv
- parent_config: experiments/manifests/m281-rejected-hidden-recovery-anchored-update.json, docs/m281-rejected-hidden-recovery-anchored-update.md
- parent_objective: design trajectory-level rejected-history retention for M267/M264
- derived_from: m281-rejected-hidden-recovery-anchored-update
- blocked_by: m281-rejected-hidden-recovery-anchored-update
- supersedes: None
- invalidates: None

## Success Criteria

- classify the M281 failure mechanism
- define how to reconstruct M272 rejected-history rollouts on M267/M264 rows
- define an anchor export that uses current M272 observations and hidden states only
- pre-register the next implementation or actor-update milestone
- no PPO or actor update is run

## Failure Criteria

- design uses old checkpoint hidden states
- design relaxes the M267/M264 success-drop gate
- PPO or actor update is run
- actor observation inputs change

## Evidence Gates

- explain why one-step rejected-hidden action anchoring failed
- define a current-family rejected-history trajectory anchor contract
- pre-register the next export or repair experiment
- do not run PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M282
- do not run a new actor update in M282
- do not loosen M267/M264 success-drop retention
- do not change actor inputs
- do not claim promotion from M281

## Failure Taxonomy

- none

## Scoreboard

- milestone: m282-current-family-rejected-trajectory-anchor-design
- type: gate
- checkpoint: runs/m281_m272_actor_coupling_m270_rejected_hidden_recovery_anchor_s10_lr5e5_seed10077/optimized_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: implement_current_family_rejected_trajectory_anchor_export
- reason: M282 designs trajectory-level M267/M264 wrong-history retention because one-step rejected-hidden anchoring does not preserve closed-loop success-drop proof

## Next Blocker

m283-current-family-rejected-trajectory-anchor-export
