# m582-bc5660-recurrent-ablation-fresh-route-eval Research Review

## Summary

- Generated at UTC: 20260524T064706Z
- Type: gate
- Gate tier: proof
- Promotion decision: bc5660_fresh_route_response_ablation_positive_admit_m583_ood
- Decision reason: M582 finds response/action ablations degrade BC5660 on fresh route; reset success drop 0.007812 margin drop 0.017594; zero-action margin drop 0.052959; zero-current and zero-all success drop 0.027344 margin drop 0.144810 collision increase 0.027344

## Hypothesis

If BC5660 uses recurrent command-response history on fresh same-distribution route seeds, reset/zero-current/zero-action ablations should degrade success, clearance margin, or collision rate relative to normal.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m578_bc_family_fresh_route_repeat_eval/summary.json, runs/m579_bc_family_moderate_ood_repeat_eval/summary.json
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: fresh-route recurrent-dependence ablation diagnostic for BC5660
- derived_from: m581-bc-recurrent-ablation-design
- blocked_by: m581-bc-recurrent-ablation-design
- supersedes: None
- invalidates: None

## Success Criteria

- benchmark completes for normal reset zero-current zero-action and zero-all policies
- seed range is 23560..23815 and no public frozen-source rows are used
- delta table reports success_drop margin_drop and collision_increase for every ablation
- diagnostic interpretation follows M581 thresholds
- research validation passes

## Failure Criteria

- benchmark fails or omits an ablation
- thresholds are changed after seeing results
- checkpoint promotion is attempted
- actor input contract changes

## Evidence Gates

- benchmark BC5660 normal reset zero-current zero-action and zero-all variants
- use fresh same-distribution seed range 23560..23815
- compute success margin and collision deltas against normal
- classify recurrent-dependence diagnostic as positive or negative
- do not promote checkpoint from ablation diagnostics

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not change checkpoint weights or actor inputs
- do not train or run PPO
- do not tune thresholds after seeing ablation results
- do not treat ablation results as promotion evidence by themselves
- do not use public frozen-source rows

## Failure Taxonomy

- none

## Scoreboard

- milestone: m582-bc5660-recurrent-ablation-fresh-route-eval
- type: gate
- checkpoint: runs/m582_bc5660_recurrent_ablation_fresh_route_eval/policy_summary.csv
- success_rate: 0.691406
- termination_rate: 0.308594
- clearance_margin_mean: 1.068165
- reset_success: 0.683594
- zero_wheel_success: None
- zero_all_success: 0.664062
- wheel_gain_mu: None
- decision: bc5660_fresh_route_response_ablation_positive_admit_m583_ood
- reason: M582 finds response/action ablations degrade BC5660 on fresh route; reset success drop 0.007812 margin drop 0.017594; zero-action margin drop 0.052959; zero-current and zero-all success drop 0.027344 margin drop 0.144810 collision increase 0.027344

## Next Blocker

m583-bc5660-recurrent-ablation-moderate-ood-eval
