# m660-action-divergent-wrong-history-corpus-design Research Review

## Summary

- Generated at UTC: 20260524T135037Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: action_divergent_wrong_history_corpus_design_admit_m661
- Decision reason: M660 designs no-training source-diverse wrong-history corpus with explicit preferred/rejected action sequences and action divergence thresholds

## Hypothesis

The current wrong-history supervision is too weak because rows are hidden-different but not action-divergent enough; a refreshed corpus with explicit rejected-history action targets is needed before further objectives.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m658_wrong_history_fusion_boundary_probe/summary.json, runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv, runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv, docs/m659-wrong-history-fusion-boundary-probe-audit.md
- parent_config: experiments/manifests/m659-wrong-history-fusion-boundary-probe-audit.json
- parent_objective: design action-divergent wrong-history corpus after M658 weak-view result
- derived_from: m659-wrong-history-fusion-boundary-probe-audit
- blocked_by: m659-wrong-history-fusion-boundary-probe-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design defines candidate inputs and selection thresholds
- design defines first-action and short-horizon divergence metrics
- design defines explicit rejected-history target fields
- design defines source-diversity and heldout split rules
- design keeps actor coupling and PPO blocked
- research validation passes

## Failure Criteria

- design admits actor training
- design omits rejected-history target/action fields
- design omits source-heldout evaluation
- design only repeats M641 hidden-difference selection

## Evidence Gates

- design source-diverse action-divergent wrong-history corpus
- require first-action and short-horizon trajectory divergence
- include explicit normal target and rejected-history target/action fields
- define source-heldout split and source dominance limits
- keep actor coupling PPO and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not update actor parameters
- do not promote checkpoint
- do not use metadata as actor input
- do not reuse M641 wrong-history rows without action-divergence filtering

## Failure Taxonomy

- none

## Scoreboard

- milestone: m660-action-divergent-wrong-history-corpus-design
- type: infrastructure
- checkpoint: docs/m660-action-divergent-wrong-history-corpus-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: action_divergent_wrong_history_corpus_design_admit_m661
- reason: M660 designs no-training source-diverse wrong-history corpus with explicit preferred/rejected action sequences and action divergence thresholds

## Next Blocker

m661-action-divergent-wrong-history-corpus-implementation
