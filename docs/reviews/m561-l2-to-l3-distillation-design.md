# m561-l2-to-l3-distillation-design Research Review

## Summary

- Generated at UTC: 20260524T051542Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: l2_to_l3_distillation_design_admit_m562_teacher_corpus_exporter
- Decision reason: M561 designs an L2 teacher to L3 recurrent student distillation path with L2 finite-window stacks training-only and canonical 72-value L3 student inputs

## Hypothesis

Because L2 is consistently strong while from-scratch L3 PPO remains contact-prone, an L2-to-L3 behavior distillation design may provide the recurrent branch with a safer policy prior before PPO continuation.

## Lineage

- parent_checkpoint: runs/m542_matched_l2_variance_seed3540/checkpoint.pt, runs/m560_l3_collision35_terminal4_seed3540/checkpoints/checkpoint_step_3584.pt, runs/m560_l3_collision35_dense002_seed3540/checkpoints/checkpoint_step_3328.pt
- parent_dataset: docs/m560-collision-margin-route-screen-selection.md, runs/m560_collision_margin_route_screen_selection/summary.json
- parent_config: configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m559_l3_collision35_terminal4_4096.json, configs/ppo_m559_l3_collision35_dense002_4096.json
- parent_objective: design supervised L2-to-L3 behavior distillation after PPO and reward-shaping L3 branches fail route-screen v2
- derived_from: m560-collision-margin-route-screen-selection
- blocked_by: m560-collision-margin-route-screen-selection
- supersedes: None
- invalidates: None

## Success Criteria

- design defines teacher/student observation boundary
- design defines distillation corpus and no-public-row selection discipline
- design defines route-screen pass/fail conditions before implementation
- research validation passes

## Failure Criteria

- design leaks L2 finite-window stack into deployable L3 actor inputs
- design uses public frozen-source rows for training or selection
- design skips route-screen v2 before public diagnostics

## Evidence Gates

- design L2 teacher to L3 recurrent student distillation without actor input changes
- keep teacher signals training-only and out of deployable actor inputs
- rotate route-screen selection seed again before any new checkpoint admission
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not feed L2 stacked observations into the deployable L3 actor
- do not add privileged hidden parameters or oracle labels
- do not select checkpoints from public frozen-source rows
- do not run public diagnostics before route-screen pass

## Failure Taxonomy

- none

## Scoreboard

- milestone: m561-l2-to-l3-distillation-design
- type: infrastructure
- checkpoint: docs/m561-l2-to-l3-distillation-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: l2_to_l3_distillation_design_admit_m562_teacher_corpus_exporter
- reason: M561 designs an L2 teacher to L3 recurrent student distillation path with L2 finite-window stacks training-only and canonical 72-value L3 student inputs

## Next Blocker

m562-l2-teacher-corpus-exporter
