# m594-bc-capability-repair-corpus-design Research Review

## Summary

- Generated at UTC: 20260524T073413Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bc_capability_repair_corpus_design_admit_runner_implementation
- Decision reason: M594 designs a closed-loop BC5660 capability corpus with P0 observations base action anchors future-response labels same-corpus pair rows and smoke metrics before training

## Hypothesis

A real capability repair smoke needs a rollout corpus that stores P0 observations, recurrent hidden states, action anchors, teacher or base actions, and future-response capability labels without leaking those labels into actor inputs.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m567_scaled_l2_teacher_corpus_train/l2_teacher_corpus.npz, runs/m567_scaled_l2_teacher_corpus_validation/l2_teacher_corpus.npz, runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv, runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: design the real capability corpus and smoke runner after M593 objective utilities
- derived_from: m593-bc-capability-repair-objective-implementation
- blocked_by: m593-bc-capability-repair-objective-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies how to collect train and validation capability rows
- design specifies how M586 matched-current pairs become ranking rows or when they must be re-mined
- design specifies action anchor source and metadata
- design pre-registers smoke metrics for regression ranking action retention and P0 metadata
- research validation passes

## Failure Criteria

- design feeds capability labels into actor inputs
- design starts real smoke training before corpus schema is registered
- design omits validation split or action-retention checks
- design promotes a checkpoint

## Evidence Gates

- design real rollout capability corpus before smoke training
- define action anchors and future-response labels without actor input leakage
- define train validation and pair-ranking splits
- pre-register smoke metrics and blockers

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train or run PPO
- do not promote checkpoint
- do not reconstruct labels from hidden vehicle parameters as actor inputs
- do not reuse private holdout for tuning
- do not claim driver performance from corpus design

## Failure Taxonomy

- none

## Scoreboard

- milestone: m594-bc-capability-repair-corpus-design
- type: infrastructure
- checkpoint: docs/m594-bc-capability-repair-corpus-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_capability_repair_corpus_design_admit_runner_implementation
- reason: M594 designs a closed-loop BC5660 capability corpus with P0 observations base action anchors future-response labels same-corpus pair rows and smoke metrics before training

## Next Blocker

m595-bc-capability-corpus-runner-implementation
