# m280-current-family-wrong-history-washout-audit Research Review

## Summary

- Generated at UTC: 20260522T184627Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_rejected_hidden_anchored_recovery_update
- Decision reason: M280 audits M279 washout and finds rejected hidden actions drift more than preferred actions because M279 used preferred-only snippet anchors; next update must include rejected-hidden anchors

## Hypothesis

M279 improves normal terminal margins but also makes rejected/wrong-history hidden states safer on current-family rows because the update lacks an explicit rejected-hidden retention or contrast anchor.

## Lineage

- parent_checkpoint: runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt, runs/m279_m272_actor_coupling_m270_retention_recovery_anchor_s10_lr5e5_seed10076/optimized_checkpoint.pt
- parent_dataset: runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m279_m267_m264_replay_gate_seed10070/boundary_replay_rows.csv
- parent_config: experiments/manifests/m279-recovery-anchored-actor-update.json, docs/m279-recovery-anchored-actor-update.md
- parent_objective: audit current-family wrong-history success-drop washout
- derived_from: m279-recovery-anchored-actor-update
- blocked_by: m279-recovery-anchored-actor-update
- supersedes: None
- invalidates: None

## Success Criteria

- identify the M267/M264 rows that lost wrong-history success drops
- separate normal-margin repair from wrong-history contrast washout
- decide whether the next repair should add rejected-hidden action anchors, source-aware contrast, or a current-family recovery/contrast corpus
- no PPO or actor update is run

## Failure Criteria

- M279 is promoted despite M267/M264 proof failure
- private holdout is used for repair tuning
- PPO or actor update is run
- actor observation inputs change

## Evidence Gates

- explain why M279 loses five M267/M264 wrong-history success drops
- check whether rejected-hidden action anchors or source-aware contrast should be reintroduced
- pre-register the next repair before any new actor update
- do not run PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M280
- do not run a new actor update in M280
- do not loosen the M267/M264 success-drop retention gate
- do not change actor inputs
- do not claim promotion from M279

## Failure Taxonomy

- none

## Scoreboard

- milestone: m280-current-family-wrong-history-washout-audit
- type: gate
- checkpoint: runs/m279_m272_actor_coupling_m270_retention_recovery_anchor_s10_lr5e5_seed10076/optimized_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_rejected_hidden_anchored_recovery_update
- reason: M280 audits M279 washout and finds rejected hidden actions drift more than preferred actions because M279 used preferred-only snippet anchors; next update must include rejected-hidden anchors

## Next Blocker

m281-rejected-hidden-recovery-anchored-update
