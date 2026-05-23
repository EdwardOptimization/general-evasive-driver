# m393-current-family-rejected-boundary-target-export Research Review

## Summary

- Generated at UTC: 20260523T144128Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m394_rejected_boundary_target_repair_probe
- Decision reason: M393 exports accepted collision-side rejected-history local targets for M267/M264 row15 and row6 and verifies no-update exact-repair loading; no PPO promotion or actor-input change

## Hypothesis

M391 remains bounded by M267/M264 row15 because the rejected-branch anchor uses a near-zero-margin base action; exporting local collision-side rejected-history targets should create a more useful conflict corpus for the next repair probe.

## Lineage

- parent_checkpoint: runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
- parent_dataset: docs/m392-m391-micro-promotion-utility-audit.md, runs/m390_step17_micro005_m267_m264_first_replay/boundary_replay_rows.csv, runs/m390_step17_a001_m267_m264_first_replay/boundary_replay_rows.csv, runs/m389_m267_row15_conflict_corpus/current_family_conflict_corpus.npz
- parent_config: experiments/manifests/m392-m391-micro-promotion-utility-audit.json
- parent_objective: export replay-selected rejected-history collision-side local action targets for the active M267/M264 boundary rows
- derived_from: m392-m391-micro-promotion-utility-audit
- blocked_by: m392-m391-micro-promotion-utility-audit
- supersedes: None
- invalidates: None

## Success Criteria

- search local wrong-history actions for M267/M264 row15 and row6 from the current public base
- export a refreshed conflict corpus with rejected_boundary_action set to collision-side targets when found
- record target margin improvement and action distance diagnostics
- verify no-update exact repair can load the refreshed corpus

## Failure Criteria

- no collision-side local target can be found for row15
- exported corpus violates shape finite value or action bounds
- actor contract changes
- research validation fails

## Evidence Gates

- no PPO run
- export local wrong-history collision-side targets for row15 and row6 when available
- no-update exact-repair smoke reads refreshed conflict corpus
- preserve actor input/output contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower M267/M264 thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m393-current-family-rejected-boundary-target-export
- type: infrastructure
- checkpoint: runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m394_rejected_boundary_target_repair_probe
- reason: M393 exports accepted collision-side rejected-history local targets for M267/M264 row15 and row6 and verifies no-update exact-repair loading; no PPO promotion or actor-input change

## Next Blocker

m394-rejected-boundary-target-repair-probe
