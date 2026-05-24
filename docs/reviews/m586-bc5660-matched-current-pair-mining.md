# m586-bc5660-matched-current-pair-mining Research Review

## Summary

- Generated at UTC: 20260524T070219Z
- Type: gate
- Gate tier: proof
- Promotion decision: bc5660_matched_current_pair_mining_pass_admit_action_screen
- Decision reason: M586 finds source-diverse BC5660 matched-current pair surfaces on both fresh and OOD distributions: fresh 666 accepted 192 physical 15 left steps 14 buckets; OOD 403 accepted 152 physical 14 left steps 14 buckets

## Hypothesis

BC5660 should expose source-diverse matched-current pair surfaces on at least one of the fresh route or moderate-OOD distributions, enabling outcome-based delayed/wrong-history interventions.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m585-bc5660-history-intervention-design.md
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: mine BC5660 matched-current pair surfaces for later history-intervention gates
- derived_from: m585-bc5660-history-intervention-design
- blocked_by: m585-bc5660-history-intervention-design
- supersedes: None
- invalidates: None

## Success Criteria

- fresh and OOD matched-current mining commands complete
- at least one surface has accepted pairs >= 60 physical pairs >= 10 left steps >= 5 and obstacle buckets >= 4
- preferred result is both surfaces meeting thresholds
- summary records whether each surface is admitted for M587 action screening
- research validation passes

## Failure Criteria

- both surfaces fail accepted-pair or source-diversity thresholds
- commands use old route seeds or public frozen-source rows
- thresholds are changed after seeing results
- checkpoint promotion is attempted

## Evidence Gates

- run matched_current_response_ambiguity on fresh route seeds 25560..25563
- run matched_current_response_ambiguity on moderate-OOD seeds 25660..25663
- require source-diverse accepted matched-current pairs before history interventions
- do not train update or promote a checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use public frozen-source rows
- do not change checkpoint weights or actor inputs
- do not loosen source-diversity thresholds after seeing results
- do not run history intervention if no source-diverse pair surface is found
- do not promote checkpoint from pair mining

## Failure Taxonomy

- none

## Scoreboard

- milestone: m586-bc5660-matched-current-pair-mining
- type: gate
- checkpoint: runs/m586_bc5660_matched_current_fresh_seed25560/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc5660_matched_current_pair_mining_pass_admit_action_screen
- reason: M586 finds source-diverse BC5660 matched-current pair surfaces on both fresh and OOD distributions: fresh 666 accepted 192 physical 15 left steps 14 buckets; OOD 403 accepted 152 physical 14 left steps 14 buckets

## Next Blocker

m587-bc5660-history-intervention-action-screen
