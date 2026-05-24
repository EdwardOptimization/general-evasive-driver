# m568-scaled-bc-training Research Review

## Summary

- Generated at UTC: 20260524T055057Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: scaled_bc_training_pass_admit_m569_route_screen_selection
- Decision reason: M568 trains three scaled BC seeds; all improve train/validation MSE and preserve P0 L3 metadata without PPO route-screen or promotion

## Hypothesis

The scaled L2 teacher corpora should train a stable L3 online-GRU BC seed family with improved train and validation action MSE while preserving the clean P0 actor contract.

## Lineage

- parent_checkpoint: runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m567_scaled_l2_teacher_corpus_train/l2_teacher_corpus.npz, runs/m567_scaled_l2_teacher_corpus_validation/l2_teacher_corpus.npz
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: train scaled L3 behavior-cloning seed family from non-public L2 teacher corpora
- derived_from: m567-scaled-teacher-corpus-export
- blocked_by: m567-scaled-teacher-corpus-export
- supersedes: None
- invalidates: None

## Success Criteria

- three BC seed runs complete
- train and validation MSE improve for all three seeds
- all checkpoints declare P0 L3 online-GRU metadata
- research validation passes

## Failure Criteria

- any seed fails to improve validation MSE
- any checkpoint violates P0 L3 metadata
- route-screen or PPO is run in this milestone

## Evidence Gates

- train BC seeds 5660 5661 5662
- verify train and validation action MSE improve for every seed
- preserve P0 L3 online-GRU checkpoint metadata
- do not run PPO route-screen or checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train on public frozen-source rows
- do not use L2 stacked observations as student inputs
- do not select by public diagnostics
- do not run route-screen or PPO in this milestone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m568-scaled-bc-training
- type: infrastructure
- checkpoint: runs/m568_scaled_l3_bc_seed5661/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: scaled_bc_training_pass_admit_m569_route_screen_selection
- reason: M568 trains three scaled BC seeds; all improve train/validation MSE and preserve P0 L3 metadata without PPO route-screen or promotion

## Next Blocker

m569-scaled-bc-route-screen-selection
