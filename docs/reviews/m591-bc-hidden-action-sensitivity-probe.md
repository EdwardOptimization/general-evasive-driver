# m591-bc-hidden-action-sensitivity-probe Research Review

## Summary

- Generated at UTC: 20260524T072431Z
- Type: gate
- Gate tier: process
- Promotion decision: bc_hidden_action_sensitivity_probe_negative_admit_hidden_use_objective_design
- Decision reason: M591 finds non-trivial hidden fusion weights but real wrong/delayed hidden action distances remain tiny on fresh and OOD surfaces while zero-current dominates; M592 objective design admitted

## Hypothesis

BC5660 will remain action-insensitive to real wrong/delayed rollout hidden states, but the probe will reveal whether that is due to hidden-head ignorance, action-equivalent real hidden states, or weak matched-current surfaces.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m568_scaled_l3_bc_seed5661/checkpoint.pt, runs/m568_scaled_l3_bc_seed5662/checkpoint.pt
- parent_dataset: runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv, runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: measure hidden-action sensitivity after M590 design
- derived_from: m590-bc-hidden-action-sensitivity-probe-design
- blocked_by: m590-bc-hidden-action-sensitivity-probe-design
- supersedes: None
- invalidates: None

## Success Criteria

- probe writes summary.json weight_chunk_summary.csv action_sensitivity_rows.csv variant_summary.csv and correlation_summary.csv
- all three scaled BC seeds have fusion weight chunk summaries
- BC5660 fresh and OOD surfaces include normal reset delayed wrong shuffled scaled random zero-current and zero-action summaries
- milestone doc applies the pre-registered M590 interpretation rules
- research validation and focused tests pass

## Failure Criteria

- probe cannot reconstruct M586 snapshots
- probe changes actor input contract
- probe reports random-hidden action movement as self-ID proof
- probe promotes a checkpoint

## Evidence Gates

- write fusion weight chunk summaries for BC5660 BC5661 and BC5662
- run BC5660 hidden-variant probe on M586 fresh and OOD matched-current surfaces
- write hidden-distance action-distance correlation summaries
- classify the hidden-use bottleneck without promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train or run PPO
- do not promote checkpoint
- do not change actor inputs
- do not treat random-hidden sensitivity as self-ID proof
- do not claim BC5661 or BC5662 matched-current wrong-history evidence from BC5660-only pair surfaces

## Failure Taxonomy

- none

## Scoreboard

- milestone: m591-bc-hidden-action-sensitivity-probe
- type: gate
- checkpoint: runs/m591_bc_hidden_action_sensitivity_probe_fresh/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_hidden_action_sensitivity_probe_negative_admit_hidden_use_objective_design
- reason: M591 finds non-trivial hidden fusion weights but real wrong/delayed hidden action distances remain tiny on fresh and OOD surfaces while zero-current dominates; M592 objective design admitted

## Next Blocker

m592-bc-hidden-use-repair-objective-design
