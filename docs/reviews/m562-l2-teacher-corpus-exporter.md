# m562-l2-teacher-corpus-exporter Research Review

## Summary

- Generated at UTC: 20260524T052117Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: l2_teacher_corpus_exporter_pass_admit_m563_l3_bc_optimizer
- Decision reason: M562 exports 116 smoke transitions with student_obs_seq shape 116x72 teacher_action_seq shape 116x3 and no teacher_obs_stack_seq in the NPZ

## Hypothesis

A corpus exporter with explicit teacher/student boundaries can create safe L2-to-L3 distillation data without contaminating the deployable L3 actor input contract.

## Lineage

- parent_checkpoint: runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: docs/m561-l2-to-l3-distillation-design.md
- parent_config: configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: export L2 teacher action targets for L3 recurrent student distillation
- derived_from: m561-l2-to-l3-distillation-design
- blocked_by: m561-l2-to-l3-distillation-design
- supersedes: None
- invalidates: None

## Success Criteria

- exporter writes student_obs_seq, teacher_action_seq, done_seq, and diagnostics
- tests verify student observation dimension is the canonical 72-value P0 frame
- tests verify teacher stack is absent from student input arrays
- research validation passes

## Failure Criteria

- exporter leaks L2 stacked observations into student input
- exporter uses public frozen-source rows
- exporter omits done masks needed for recurrent hidden reset

## Evidence Gates

- implement corpus exporter with L2 teacher targets and L3 72-value student observations
- write tests that prevent L2 stack leakage into student input tensor
- use non-public training/validation route seeds
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use public frozen-source rows
- do not store privileged hidden parameters as student inputs
- do not feed L2 finite-window stack to deployed L3 actor
- do not train a student in this milestone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m562-l2-teacher-corpus-exporter
- type: infrastructure
- checkpoint: runs/m562_l2_teacher_corpus_exporter_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: l2_teacher_corpus_exporter_pass_admit_m563_l3_bc_optimizer
- reason: M562 exports 116 smoke transitions with student_obs_seq shape 116x72 teacher_action_seq shape 116x3 and no teacher_obs_stack_seq in the NPZ

## Next Blocker

m563-l3-behavior-cloning-optimizer
