# m564-bc-route-screen-v2-smoke Research Review

## Summary

- Generated at UTC: 20260524T053024Z
- Type: gate
- Gate tier: proof
- Promotion decision: bc_route_screen_v2_pass_admit_m565_public_surface_eval
- Decision reason: M564 admits M563_BC for public diagnostics because it matches L2 success/collision and strongly beats L0 on fresh route-screen seed 17560

## Hypothesis

If L2-to-L3 behavior cloning transfers enough of the L2 safe action prior, the M563 BC checkpoint should clear at least the L0 route-screen v2 success, margin, and collision gates on fresh seed 17560.

## Lineage

- parent_checkpoint: runs/m563_l3_behavior_cloning_smoke/checkpoint.pt, runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m562_l2_teacher_corpus_exporter_smoke/l2_teacher_corpus.npz, runs/m563_l2_teacher_corpus_validation_smoke/l2_teacher_corpus.npz
- parent_config: configs/ppo_m541_matched_l0_variance_4096.json, configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: route-screen v2 diagnostic for the M563 L3 BC smoke checkpoint
- derived_from: m563-l3-behavior-cloning-optimizer
- blocked_by: m563-l3-behavior-cloning-optimizer
- supersedes: None
- invalidates: None

## Success Criteria

- route-screen v2 artifact is written with uses_public_frozen_source_rows=false
- M563 BC candidate is compared to L0 and L2 references under level-matched configs
- candidate passes L0 binary success, L0 margin, and collision tolerance checks
- research validation passes

## Failure Criteria

- candidate fails L0 route-screen v2 gates
- route-screen uses public frozen-source rows
- selection uses M556 or M560 route-screen seeds
- checkpoint is promoted from this smoke alone

## Evidence Gates

- evaluate M563 BC smoke checkpoint with route-screen v2 seed 17560
- compare against level-matched L0 and L2 references
- do not run public frozen-source diagnostics unless route-screen admits the candidate
- do not promote checkpoint from this smoke alone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use M556 seed 15560 or M560 seed 16560 for selection
- do not use public frozen-source rows
- do not tune from route-screen output inside this milestone
- do not promote without later proof/generalization gates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m564-bc-route-screen-v2-smoke
- type: gate
- checkpoint: runs/m564_bc_route_screen_v2_smoke/summary.json
- success_rate: 0.65625
- termination_rate: 0.34375
- clearance_margin_mean: 0.770803
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_route_screen_v2_pass_admit_m565_public_surface_eval
- reason: M564 admits M563_BC for public diagnostics because it matches L2 success/collision and strongly beats L0 on fresh route-screen seed 17560

## Next Blocker

m565-bc-public-natural-surface-eval
