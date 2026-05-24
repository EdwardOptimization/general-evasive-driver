# m566-scaled-bc-repeat-design Research Review

## Summary

- Generated at UTC: 20260524T054354Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: scaled_bc_repeat_design_admit_m567_scaled_teacher_corpus_export
- Decision reason: M566 designs scaled non-public BC repeat with fresh train/validation seeds optimizer repeats and route-screen seed 18560 while keeping PPO blocked

## Hypothesis

Because a tiny M563 BC smoke repaired the M543 public-surface L3 regression, a scaled non-public L2-to-L3 BC repeat should test whether the effect is stable across corpus size and optimizer seeds before PPO continuation.

## Lineage

- parent_checkpoint: runs/m563_l3_behavior_cloning_smoke/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m565_bc_public_natural_surface_eval_aggregate/summary.json, runs/m562_l2_teacher_corpus_exporter_smoke/l2_teacher_corpus.npz, runs/m563_l2_teacher_corpus_validation_smoke/l2_teacher_corpus.npz
- parent_config: configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: design scaled non-public L2-to-L3 behavior-cloning repeat after positive public diagnostics
- derived_from: m565-bc-public-natural-surface-eval
- blocked_by: m565-bc-public-natural-surface-eval
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies train/validation seed splits and fresh route-screen seed
- design specifies BC seed repeats and selection rule
- design preserves P0 L3 actor contract and L2 stack training-only boundary
- research validation passes

## Failure Criteria

- design tunes from public frozen-source rows
- design reuses M564 route-screen seed for new checkpoint selection
- design allows PPO before scaled BC evidence is stable

## Evidence Gates

- design larger non-public train and validation corpora for L2-to-L3 BC
- design multi-seed BC repeat and fresh route-screen selection
- keep public frozen-source surfaces out of training and checkpoint tuning
- keep PPO blocked until scaled BC route/generalization evidence is stable

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train from public frozen-source rows
- do not tune directly from M565 public-surface residuals
- do not reuse route-screen seed 17560 for new selection
- do not promote from public diagnostics alone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m566-scaled-bc-repeat-design
- type: infrastructure
- checkpoint: docs/m566-scaled-bc-repeat-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: scaled_bc_repeat_design_admit_m567_scaled_teacher_corpus_export
- reason: M566 designs scaled non-public BC repeat with fresh train/validation seeds optimizer repeats and route-screen seed 18560 while keeping PPO blocked

## Next Blocker

m567-scaled-teacher-corpus-export
