# m658-wrong-history-fusion-boundary-probe-implementation Research Review

## Summary

- Generated at UTC: 20260524T134510Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: wrong_history_fusion_boundary_probe_negative_admit_audit
- Decision reason: M658 finds no passing diagnostic view; next_hidden gives relative L2 improvement but absolute wrong-history gap remains too weak

## Hypothesis

A diagnostic head trained on next_hidden or fused_plus_next_hidden will create stronger wrong-history separation than one trained on fused actor features if M655's blocker is the response/context fusion boundary.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz, runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv, runs/m655_wrong_history_feature_separability_audit/summary.json, docs/m657-wrong-history-fusion-boundary-probe-design.md
- parent_config: experiments/manifests/m657-wrong-history-fusion-boundary-probe-design.json
- parent_objective: implement frozen feature-view comparison probe
- derived_from: m657-wrong-history-fusion-boundary-probe-design
- blocked_by: m657-wrong-history-fusion-boundary-probe-design
- supersedes: None
- invalidates: None

## Success Criteria

- all actor checksums unchanged
- no actor checkpoint written
- fused next_hidden and fused_plus_next_hidden views are all evaluated
- at least one pre-fusion or concat view creates stronger source-heldout wrong-history separation than fused baseline
- source 30 and source 32 summaries are written
- research validation passes

## Failure Criteria

- actor checksum changes
- actor checkpoint is written
- fused baseline is omitted
- source-heldout wrong-history rows are omitted
- results are interpreted as promotion

## Evidence Gates

- train only diagnostic auxiliary heads for fused next_hidden and fused_plus_next_hidden views
- run seeds 6570 6571 6572
- report normal retention and wrong-history gaps by view
- verify actor checksum unchanged and no actor checkpoint written
- compare next_hidden and concat views against same-run fused baseline

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update actor parameters
- do not run PPO
- do not promote checkpoint
- do not use metadata as actor or head input
- do not skip the fused-view baseline
- do not treat auxiliary head success as closed-loop self-ID proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m658-wrong-history-fusion-boundary-probe-implementation
- type: infrastructure
- checkpoint: runs/m658_wrong_history_fusion_boundary_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: wrong_history_fusion_boundary_probe_negative_admit_audit
- reason: M658 finds no passing diagnostic view; next_hidden gives relative L2 improvement but absolute wrong-history gap remains too weak

## Next Blocker

m659-wrong-history-fusion-boundary-probe-audit
