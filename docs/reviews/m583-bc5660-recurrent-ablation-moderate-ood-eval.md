# m583-bc5660-recurrent-ablation-moderate-ood-eval Research Review

## Summary

- Generated at UTC: 20260524T065112Z
- Type: gate
- Gate tier: proof
- Promotion decision: bc5660_ood_response_ablation_positive_admit_m584_audit
- Decision reason: M583 repeats current-response degradation on moderate-OOD; reset success drop 0.003906 margin drop 0.012892; zero-action remains weak margin drop 0.036946; zero-current and zero-all success drop 0.035156 margin drop 0.100321 collision increase 0.035156

## Hypothesis

If the M582 response/action dependence is not only a same-distribution route artifact, BC5660 ablations should also degrade success, clearance margin, or collision rate on fresh moderate-OOD route seeds.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m582_bc5660_recurrent_ablation_fresh_route_eval/policy_summary.csv, runs/m579_bc_family_moderate_ood_repeat_eval/summary.json
- parent_config: configs/eval_m574_moderate_ood_l3.json
- parent_objective: moderate-OOD recurrent-dependence ablation diagnostic for BC5660
- derived_from: m582-bc5660-recurrent-ablation-fresh-route-eval
- blocked_by: m582-bc5660-recurrent-ablation-fresh-route-eval
- supersedes: None
- invalidates: None

## Success Criteria

- benchmark completes for normal reset zero-current zero-action and zero-all policies
- seed range is 24560..24815 and no public frozen-source rows are used
- delta table reports success_drop margin_drop and collision_increase for every ablation
- diagnostic interpretation follows the unchanged M581 thresholds
- research validation passes

## Failure Criteria

- benchmark fails or omits an ablation
- thresholds are changed after seeing results
- checkpoint promotion is attempted
- actor input contract changes

## Evidence Gates

- benchmark BC5660 normal reset zero-current zero-action and zero-all variants on moderate-OOD route seeds
- use fresh moderate-OOD seed range 24560..24815
- compute success margin and collision deltas against normal
- classify recurrent-dependence diagnostic using the M581 thresholds without retuning
- do not promote checkpoint from ablation diagnostics

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not change checkpoint weights or actor inputs
- do not train or run PPO
- do not tune thresholds after seeing M582 or M583 results
- do not treat ablation results as promotion evidence by themselves
- do not use public frozen-source rows

## Failure Taxonomy

- none

## Scoreboard

- milestone: m583-bc5660-recurrent-ablation-moderate-ood-eval
- type: gate
- checkpoint: runs/m583_bc5660_recurrent_ablation_moderate_ood_eval/policy_summary.csv
- success_rate: 0.621094
- termination_rate: 0.378906
- clearance_margin_mean: 0.985368
- reset_success: 0.617188
- zero_wheel_success: None
- zero_all_success: 0.585938
- wheel_gain_mu: None
- decision: bc5660_ood_response_ablation_positive_admit_m584_audit
- reason: M583 repeats current-response degradation on moderate-OOD; reset success drop 0.003906 margin drop 0.012892; zero-action remains weak margin drop 0.036946; zero-current and zero-all success drop 0.035156 margin drop 0.100321 collision increase 0.035156

## Next Blocker

m584-bc-recurrent-ablation-audit
