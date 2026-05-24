# m563-l3-behavior-cloning-optimizer Research Review

## Summary

- Generated at UTC: 20260524T052718Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: l3_bc_optimizer_pass_admit_m564_route_screen_smoke
- Decision reason: M563 offline BC reduces train action MSE 0.083840 to 0.0000705 and validation MSE 0.076715 to 0.000131 while preserving P0 L3 metadata

## Hypothesis

An offline behavior-cloning optimizer can transfer the strong L2 finite-window action prior into an L3 online-GRU actor while keeping the deployable P0 actor contract clean.

## Lineage

- parent_checkpoint: runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m562_l2_teacher_corpus_exporter_smoke/l2_teacher_corpus.npz, docs/m562-l2-teacher-corpus-exporter.md
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: offline behavior cloning from L2 teacher targets into an L3 online-GRU student
- derived_from: m562-l2-teacher-corpus-exporter
- blocked_by: m562-l2-teacher-corpus-exporter
- supersedes: None
- invalidates: None

## Success Criteria

- optimizer loads M562-style student_obs_seq and teacher_action_seq arrays
- optimizer trains an L3 online-GRU checkpoint with P0 72-value inputs
- train and validation teacher-action MSE improve versus initialization
- tests cover recurrent hidden reset masks and student input dimension checks
- research validation passes

## Failure Criteria

- optimizer consumes teacher stacked observations as student input
- checkpoint metadata no longer declares P0 L3 online-GRU
- validation MSE does not improve in the smoke run
- optimizer runs PPO or route-screen selection in this milestone

## Evidence Gates

- implement offline L3 behavior-cloning optimizer from M562-style corpora
- preserve P0 72-value student input and L3 online-GRU metadata
- write train and validation action MSE artifacts
- do not run PPO or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train from public frozen-source rows
- do not feed L2 stacked observations into the L3 student
- do not add hidden parameters or oracle labels
- do not promote a checkpoint before route-screen v2

## Failure Taxonomy

- none

## Scoreboard

- milestone: m563-l3-behavior-cloning-optimizer
- type: infrastructure
- checkpoint: runs/m563_l3_behavior_cloning_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: l3_bc_optimizer_pass_admit_m564_route_screen_smoke
- reason: M563 offline BC reduces train action MSE 0.083840 to 0.0000705 and validation MSE 0.076715 to 0.000131 while preserving P0 L3 metadata

## Next Blocker

m564-bc-route-screen-v2-smoke
