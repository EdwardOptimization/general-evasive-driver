# m644-source-balanced-bc-v2-objective-implementation Research Review

## Summary

- Generated at UTC: 20260524T124631Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_balanced_bc_v2_objective_implementation_pass_admit_head_only_design
- Decision reason: M644 implements exact no-update BC-v2 evaluator with normal loss 0.002101438 variant loss 0.002599709 unchanged actor checksum and separate source split target summaries

## Hypothesis

The M641 corpus and BC5660 checkpoint can be evaluated by an exact BC-v2 objective that separates normal and variant hidden action losses without changing the actor.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz, runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv, runs/m642_sequence_corpus_exact_objective_sanity/summary.json, docs/m643-source-balanced-bc-v2-objective-design.md
- parent_config: experiments/manifests/m643-source-balanced-bc-v2-objective-design.json
- parent_objective: implement exact source-balanced BC-v2 objective/evaluator before any optimizer
- derived_from: m643-source-balanced-bc-v2-objective-design
- blocked_by: m643-source-balanced-bc-v2-objective-design
- supersedes: None
- invalidates: None

## Success Criteria

- exact evaluator writes row/source/split/target summaries
- normal-hidden and variant-hidden first-action losses are both reported
- source-balanced sequence delta metrics are finite
- actor parameter checksum is unchanged
- no checkpoint is written
- research validation passes

## Failure Criteria

- evaluator starts an optimizer
- actor parameters change
- normal and variant hidden metrics are collapsed
- source-balanced summaries are missing
- non-finite objective metrics are written

## Evidence Gates

- load M641 corpus and M568 BC5660 checkpoint
- compute normal-hidden first-action target loss
- compute variant-hidden first-action target loss
- compute source-balanced sequence delta target metrics
- write source split and target summaries
- confirm actor parameters are unchanged

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not mutate actor parameters
- do not use metadata as actor input
- do not collapse source-balanced weights

## Failure Taxonomy

- none

## Scoreboard

- milestone: m644-source-balanced-bc-v2-objective-implementation
- type: infrastructure
- checkpoint: runs/m644_source_balanced_bc_v2_objective/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_balanced_bc_v2_objective_implementation_pass_admit_head_only_design
- reason: M644 implements exact no-update BC-v2 evaluator with normal loss 0.002101438 variant loss 0.002599709 unchanged actor checksum and separate source split target summaries

## Next Blocker

m645-bc-v2-head-only-smoke-design
