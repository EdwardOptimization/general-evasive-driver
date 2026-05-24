# m590-bc-hidden-action-sensitivity-probe-design Research Review

## Summary

- Generated at UTC: 20260524T071828Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bc_hidden_action_sensitivity_probe_design_admit_m591_probe
- Decision reason: M590 pre-registers hidden perturbation variants fusion weight chunk norms hidden-action correlations artifacts and interpretation rules before implementation

## Hypothesis

A targeted hidden-action sensitivity probe can explain whether BC5660 lacks hidden-history action signal because the actor head ignores hidden features, real rollout hidden states are action-equivalent, or the M586/M587 matched-current surface is too weak.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m568_scaled_l3_bc_seed5661/checkpoint.pt, runs/m568_scaled_l3_bc_seed5662/checkpoint.pt
- parent_dataset: runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv, runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv, runs/m587_bc5660_history_action_screen_fresh_seed25560/variant_summary.csv, runs/m587_bc5660_history_action_screen_ood_seed25660/variant_summary.csv
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: design a hidden-action sensitivity probe after M589 finds a one-step BC objective bottleneck
- derived_from: m589-bc-hidden-use-objective-audit
- blocked_by: m589-bc-hidden-use-objective-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies exact hidden perturbation variants and metrics
- design specifies how to compute fusion weight chunk norms and hidden/action distance correlations
- design specifies comparison across BC5660 BC5661 and BC5662
- design states pass/fail interpretations before any probe run
- research validation passes

## Failure Criteria

- design changes the actor input contract
- design treats random-hidden action sensitivity as sufficient self-ID proof
- design starts repair training before measuring hidden-use sensitivity
- design promotes a checkpoint

## Evidence Gates

- design hidden perturbation metrics before implementation
- separate structural hidden path from empirical hidden-state use
- pre-register normal reset zero delayed wrong shuffled scaled and random hidden variants
- preserve the P0 human-view no-wheel no-oracle actor contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train or run PPO
- do not promote checkpoint
- do not add hidden vehicle parameters or wheel/slip features to actor inputs
- do not claim self-ID from route performance or random-hidden sensitivity alone
- do not use private holdout evidence for probe tuning

## Failure Taxonomy

- none

## Scoreboard

- milestone: m590-bc-hidden-action-sensitivity-probe-design
- type: infrastructure
- checkpoint: docs/m590-bc-hidden-action-sensitivity-probe-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_hidden_action_sensitivity_probe_design_admit_m591_probe
- reason: M590 pre-registers hidden perturbation variants fusion weight chunk norms hidden-action correlations artifacts and interpretation rules before implementation

## Next Blocker

m591-bc-hidden-action-sensitivity-probe
