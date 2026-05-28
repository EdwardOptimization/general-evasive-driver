# m1187-paper-route-l0-l1-l2-l3-controller-comparison-design Research Review

## Summary

- Generated at UTC: 20260528T041450Z
- Type: gate
- Gate tier: process
- Promotion decision: l0_l1_l2_l3_controller_comparison_design_admit_profile_scaffold
- Decision reason: M1187 defines fair L0 current-masked L1 one-step L2 finite-window and L3 online-GRU comparison plus task families splits metrics and gate triggers without training replay PPO promotion private holdout or actor-input change

## Hypothesis

A fair L0/L1/L2/L3 comparison design can separate current-response feedback, finite-window history, and GRU recurrent belief before training or paper claims.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/paper-route-finite-window-vs-gru-plan.md, docs/active-gate-policy.md, docs/m1186-paper-route-active-gate-policy-design.md
- parent_config: experiments/manifests/m1186-paper-route-active-gate-policy-design.json
- parent_objective: design a fair L0 L1 L2 L3 controller comparison before any GRU-first paper claim or controller training
- derived_from: m1182a-v4-public-base-paper-route-finite-window-gru-plan, m1186-paper-route-active-gate-policy-design
- blocked_by: paper route needs fair current feedback finite-window and GRU comparison before training or recurrent-belief claims
- supersedes: assuming the online GRU is the mainline answer without finite-window baselines
- invalidates: training L3 only before fixing L0 L1 L2 baselines and gate usage, claiming self-identification from GRU success without finite-window comparison

## Success Criteria

- docs/m1187-paper-route-l0-l1-l2-l3-controller-comparison-design.md exists
- controller variants L0 L1 L2 L3 are specified
- finite-window lengths are specified
- same deployable actor-input contract is specified for all variants
- capacity and inference-cost controls are specified
- task families and train/eval splits are specified
- gate policy from docs/active-gate-policy.md is applied
- no controller training, candidate replay, PPO, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- design gives hidden or oracle actor inputs to any variant
- design omits finite-window baselines
- design does not specify task splits or gate usage
- controller training, candidate replay, PPO, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1187 may design controller families and evaluation splits only
- M1187 must not train controller weights
- M1187 must not run candidate replay
- M1187 must not run PPO
- M1187 must not promote
- M1187 must not use private holdout
- M1187 must not change actor-input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train L0 L1 L2 or L3
- do not run PPO
- do not run private holdout
- do not change actor inputs
- do not give any actor hidden or oracle inputs
- do not claim GRU superiority from design
- do not skip finite-window baselines

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1187-paper-route-l0-l1-l2-l3-controller-comparison-design
- type: gate
- checkpoint: docs/m1187-paper-route-l0-l1-l2-l3-controller-comparison-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: l0_l1_l2_l3_controller_comparison_design_admit_profile_scaffold
- reason: M1187 defines fair L0 current-masked L1 one-step L2 finite-window and L3 online-GRU comparison plus task families splits metrics and gate triggers without training replay PPO promotion private holdout or actor-input change

## Next Blocker

m1188-paper-route-controller-profile-scaffold-implementation
