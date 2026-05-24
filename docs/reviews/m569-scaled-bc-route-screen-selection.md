# m569-scaled-bc-route-screen-selection Research Review

## Summary

- Generated at UTC: 20260524T055339Z
- Type: gate
- Gate tier: proof
- Promotion decision: scaled_bc_route_screen_pass_admit_m570_public_surface_eval
- Decision reason: M569 route-screen seed 18560 passes all three scaled BC candidates and selects BC5660 by highest clearance margin without promotion

## Hypothesis

If scaled L2-to-L3 BC is stable, at least one M568 seed should clear route-screen v2 against L0 and remain L2-competitive on fresh selection seed 18560.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m568_scaled_l3_bc_seed5661/checkpoint.pt, runs/m568_scaled_l3_bc_seed5662/checkpoint.pt, runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m567_scaled_l2_teacher_corpus_train/l2_teacher_corpus.npz, runs/m567_scaled_l2_teacher_corpus_validation/l2_teacher_corpus.npz
- parent_config: configs/ppo_m541_matched_l0_variance_4096.json, configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: route-screen v2 selection for scaled L3 BC seed family
- derived_from: m568-scaled-bc-training
- blocked_by: m568-scaled-bc-training
- supersedes: None
- invalidates: None

## Success Criteria

- route-screen v2 artifact is written with uses_public_frozen_source_rows=false
- all three M568 candidates are compared to L0 and L2 under level-matched configs
- at least one candidate passes L0 success margin and collision tolerance
- selected candidate is recorded without checkpoint promotion
- research validation passes

## Failure Criteria

- no candidate passes L0 route-screen v2 gates
- route-screen reuses seed 17560
- public frozen-source rows are used
- checkpoint is promoted from route-screen alone

## Evidence Gates

- evaluate M568 BC seeds 5660 5661 5662 with route-screen v2 seed 18560
- compare against level-matched L0 and L2 references
- select only if candidate passes L0 success margin and collision gates
- do not run public frozen-source diagnostics or promote checkpoint in this milestone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not reuse route-screen seed 17560
- do not use public frozen-source rows
- do not tune M568 checkpoints from route-screen output inside this milestone
- do not promote without later public/generalization gates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m569-scaled-bc-route-screen-selection
- type: gate
- checkpoint: runs/m569_scaled_bc_route_screen_selection/summary.json
- success_rate: 0.671875
- termination_rate: 0.328125
- clearance_margin_mean: 0.950870
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: scaled_bc_route_screen_pass_admit_m570_public_surface_eval
- reason: M569 route-screen seed 18560 passes all three scaled BC candidates and selects BC5660 by highest clearance margin without promotion

## Next Blocker

m570-scaled-bc-public-natural-surface-eval
