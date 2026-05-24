# m567-scaled-teacher-corpus-export Research Review

## Summary

- Generated at UTC: 20260524T054647Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: scaled_teacher_corpus_export_pass_admit_m568_scaled_bc_training
- Decision reason: M567 exports scaled train and validation L2 teacher corpora with 8024 and 3900 transitions using canonical 72-value student frames and no teacher stack arrays

## Hypothesis

Scaled non-public L2 teacher corpora can be exported with the same clean teacher/student boundary as M562, enabling multi-seed L3 BC repeat without public-row contamination.

## Lineage

- parent_checkpoint: runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: docs/m566-scaled-bc-repeat-design.md
- parent_config: configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: export scaled non-public L2 teacher corpora for L3 behavior cloning repeat
- derived_from: m566-scaled-bc-repeat-design
- blocked_by: m566-scaled-bc-repeat-design
- supersedes: None
- invalidates: None

## Success Criteria

- train and validation corpora are exported
- student_obs_dim is 72 for both corpora
- teacher_stack_stored is false for both corpora
- transition counts exceed the M562/M563 smoke corpora
- research validation passes

## Failure Criteria

- exporter leaks teacher stack into student arrays
- public frozen-source rows are used
- corpus export fails or produces empty transition arrays

## Evidence Gates

- export train corpus seeds 18200-18327
- export validation corpus seeds 18328-18391
- verify canonical 72-value student observations and absent teacher stack arrays
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use public frozen-source rows
- do not reuse M562/M563 smoke corpora as scaled repeat evidence
- do not train a BC student in this milestone
- do not store L2 stack as a student input

## Failure Taxonomy

- none

## Scoreboard

- milestone: m567-scaled-teacher-corpus-export
- type: infrastructure
- checkpoint: runs/m567_scaled_l2_teacher_corpus_train/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: scaled_teacher_corpus_export_pass_admit_m568_scaled_bc_training
- reason: M567 exports scaled train and validation L2 teacher corpora with 8024 and 3900 transitions using canonical 72-value student frames and no teacher stack arrays

## Next Blocker

m568-scaled-bc-training
