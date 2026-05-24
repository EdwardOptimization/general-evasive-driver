# m585-bc5660-history-intervention-design Research Review

## Summary

- Generated at UTC: 20260524T065826Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bc5660_history_intervention_design_admit_pair_mining
- Decision reason: M585 selects existing matched-current action-intervention and persistent wrong-history tools for a staged outcome-based BC5660 history diagnostic; M586 will mine source-diverse pairs

## Hypothesis

Because current-response ablations are positive but reset-hidden ablations are weak, the next diagnostic should directly intervene on delayed or wrong recurrent history while holding current observation and scene as fixed as possible.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m582_bc5660_recurrent_ablation_fresh_route_eval/policy_summary.csv, runs/m583_bc5660_recurrent_ablation_moderate_ood_eval/policy_summary.csv
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: design a causal history-intervention diagnostic after reset-hidden ablation was weak
- derived_from: m584-bc-recurrent-ablation-audit
- blocked_by: m584-bc-recurrent-ablation-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design identifies the concrete existing tool path or scoped tool gap for BC5660 history intervention
- design specifies normal reset delayed wrong-history and zero-current controls
- design specifies accepted-row and outcome-degradation thresholds before any run
- design classifies possible negative outcomes without promotion or PPO
- research validation passes

## Failure Criteria

- design relies on hidden vehicle parameters as deployable actor inputs
- design only measures action distance and omits closed-loop outcome checks
- design starts evaluation before thresholds are registered
- design promotes a checkpoint

## Evidence Gates

- inspect existing wrong-history delayed-history and persistent-intervention tooling
- design a BC5660 history-intervention gate that holds current scene fixed as much as possible
- pre-register source snapshots accepted-row thresholds controls and failure taxonomy
- do not train evaluate or promote in design milestone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use hidden vehicle parameters as actor inputs
- do not claim self-ID from action difference without outcome degradation
- do not promote from design-only evidence
- do not run PPO or behavior cloning
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m585-bc5660-history-intervention-design
- type: infrastructure
- checkpoint: docs/m585-bc5660-history-intervention-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc5660_history_intervention_design_admit_pair_mining
- reason: M585 selects existing matched-current action-intervention and persistent wrong-history tools for a staged outcome-based BC5660 history diagnostic; M586 will mine source-diverse pairs

## Next Blocker

m586-bc5660-matched-current-pair-mining
