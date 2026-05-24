# m547-l3-recurrent-repair-route-pilot Research Review

## Summary

- Generated at UTC: 20260524T041122Z
- Type: gate
- Gate tier: proof
- Promotion decision: route_health_reject_training_instability_admit_m548_update_aligned_checkpoint_configs
- Decision reason: M547 finds 0 of 27 saved checkpoints pass route health and the best rollout step 1792 is unsaved by the 512-step cadence

## Hypothesis

At least one M546 L3 repair variant will pass route health by preserving interval checkpoints or reducing recurrent update aggressiveness, enabling a later public diagnostic eval.

## Lineage

- parent_checkpoint: runs/m542_matched_l3_variance_seed3540/checkpoint.pt
- parent_dataset: docs/m545-l3-recurrent-recipe-repair-design.md, docs/m546-l3-recurrent-repair-config-family.md
- parent_config: configs/ppo_m546_l3_repair_fast_select_4096.json, configs/ppo_m546_l3_repair_lr1e4_4096.json, configs/ppo_m546_l3_repair_lr5e5_4096.json
- parent_objective: run L3-only route pilot with pre-registered interval checkpoint selection
- derived_from: m546-l3-recurrent-repair-config-family
- blocked_by: m546-l3-recurrent-repair-config-family
- supersedes: None
- invalidates: None

## Success Criteria

- all three repair training runs complete with valid P0 metadata
- interval checkpoint artifacts are available for route selection
- a route-selected candidate satisfies M545 route-health criteria, or failure is classified as training_instability
- research validation passes

## Failure Criteria

- training run fails to produce valid metadata
- selection uses public frozen-source rows
- no candidate can be evaluated under the pre-registered route rule

## Evidence Gates

- run all three M546 L3 repair configs on seed 3540
- collect interval checkpoint route metrics before any public frozen-source eval
- apply M545 route-only checkpoint selection rule
- do not promote checkpoint or claim L3 beats L2

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not select checkpoint from public frozen-source rows
- do not alter configs after seeing route results
- do not compare repaired L3 as final evidence against L2 until a frozen matched rerun exists

## Failure Taxonomy

- training_instability

## Scoreboard

- milestone: m547-l3-recurrent-repair-route-pilot
- type: gate
- checkpoint: runs/m547_l3_repair_fast_select_seed3540/checkpoints/checkpoint_step_1024.pt
- success_rate: 22.941196
- termination_rate: 1.0
- clearance_margin_mean: -0.112931
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: route_health_reject_training_instability_admit_m548_update_aligned_checkpoint_configs
- reason: M547 finds 0 of 27 saved checkpoints pass route health and the best rollout step 1792 is unsaved by the 512-step cadence

## Next Blocker

m548-l3-update-aligned-checkpoint-config-family
