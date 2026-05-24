# m661-action-divergent-wrong-history-corpus-implementation Research Review

## Summary

- Generated at UTC: 20260524T140356Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: action_divergent_wrong_history_corpus_negative_admit_audit
- Decision reason: M661 writes explicit preferred/rejected corpus artifacts but accepts 0 of 3207 candidates because wrong-history sequence and margin divergence are below thresholds

## Hypothesis

A source-diverse corpus requiring action and short-horizon divergence will produce stronger wrong-history supervision than M641's hidden-different rows.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv, runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv, runs/m636_combined_source7_preserving_shape/accepted_combined_sequences.csv, docs/m660-action-divergent-wrong-history-corpus-design.md
- parent_config: experiments/manifests/m660-action-divergent-wrong-history-corpus-design.json
- parent_objective: implement no-training action-divergent wrong-history corpus
- derived_from: m660-action-divergent-wrong-history-corpus-design
- blocked_by: m660-action-divergent-wrong-history-corpus-design
- supersedes: None
- invalidates: None

## Success Criteria

- accepted rows >= 40
- accepted physical pairs >= 8
- accepted left seeds >= 6
- targets >= 2
- source-heldout split is nonempty
- mean preferred_vs_rejected_action_mean_l2 >= 0.010
- mean margin_gap >= 0.010
- actor checksum unchanged
- no actor checkpoint written
- research validation passes

## Failure Criteria

- too few accepted rows
- source diversity fails
- rejected target/action fields are missing
- actor checksum changes
- actor checkpoint is written

## Evidence Gates

- mine source-diverse action-divergent wrong-history rows
- write explicit preferred and rejected action sequences
- enforce action sequence and margin divergence thresholds
- write source split and target summaries
- verify actor checksum unchanged and no actor checkpoint written

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not update actor parameters
- do not promote checkpoint
- do not accept hidden-distance-only rows
- do not omit rejected-history target/action fields

## Failure Taxonomy

- none

## Scoreboard

- milestone: m661-action-divergent-wrong-history-corpus-implementation
- type: infrastructure
- checkpoint: runs/m661_action_divergent_wrong_history_corpus/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: action_divergent_wrong_history_corpus_negative_admit_audit
- reason: M661 writes explicit preferred/rejected corpus artifacts but accepts 0 of 3207 candidates because wrong-history sequence and margin divergence are below thresholds

## Next Blocker

m662-action-divergent-wrong-history-corpus-audit
