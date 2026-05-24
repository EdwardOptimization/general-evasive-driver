# m587-bc5660-history-intervention-action-screen Research Review

## Summary

- Generated at UTC: 20260524T070628Z
- Type: gate
- Gate tier: proof
- Promotion decision: bc5660_history_action_screen_negative_admit_failure_audit
- Decision reason: M587 rejects persistent outcome rollout: wrong and delayed history have zero above-threshold action rows on fresh and OOD surfaces while zero-current is 100 percent above threshold on both

## Hypothesis

If the M586 matched-current surfaces contain history-sensitive decision points, wrong_matched_history or delayed_history should produce non-trivial action changes before outcome rollout.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv, runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: screen BC5660 matched-current pair surfaces for delayed or wrong-history action sensitivity
- derived_from: m586-bc5660-matched-current-pair-mining
- blocked_by: m586-bc5660-matched-current-pair-mining
- supersedes: None
- invalidates: None

## Success Criteria

- fresh and OOD action-screen commands complete
- at least one surface has wrong_matched_history or delayed_history above_threshold_count >= 16 and action_distance_mean >= 0.02
- zero_current_response is reported as a positive control
- summary clearly states that M587 is an action screen only and cannot prove outcome self-ID
- research validation passes

## Failure Criteria

- both surfaces have no wrong/delayed history action signal
- action distance is treated as outcome proof
- thresholds are changed after seeing results
- checkpoint promotion is attempted

## Evidence Gates

- run matched_history_intervention_gate on the M586 fresh route pair surface
- run matched_history_intervention_gate on the M586 moderate-OOD pair surface
- screen wrong_matched_history and delayed_history action distances before outcome rollout
- do not claim self-ID from action distance alone
- do not train update or promote a checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use action distance alone as outcome proof
- do not run persistent outcome intervention if both surfaces have no wrong/delayed action signal
- do not change checkpoint weights or actor inputs
- do not retune min-action-distance after seeing results
- do not promote checkpoint from action screen

## Failure Taxonomy

- none

## Scoreboard

- milestone: m587-bc5660-history-intervention-action-screen
- type: gate
- checkpoint: runs/m587_bc5660_history_action_screen_fresh_seed25560/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc5660_history_action_screen_negative_admit_failure_audit
- reason: M587 rejects persistent outcome rollout: wrong and delayed history have zero above-threshold action rows on fresh and OOD surfaces while zero-current is 100 percent above threshold on both

## Next Blocker

m588-bc5660-history-action-screen-negative-audit
