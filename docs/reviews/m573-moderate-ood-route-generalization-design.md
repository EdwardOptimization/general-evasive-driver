# m573-moderate-ood-route-generalization-design Research Review

## Summary

- Generated at UTC: 20260524T061214Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: moderate_ood_route_design_admit_m574_config_family
- Decision reason: M573 pre-registers eval-only moderate-OOD config deltas seed range 20560..20815 and relaxed L2 competitiveness tolerances before any OOD eval

## Hypothesis

Because BC5660 passed a larger fresh route/generalization gate, the next evidence layer should test moderate OOD route robustness with pre-registered eval-only configs before any PPO continuation.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m572_fresh_route_generalization_eval/summary.json, runs/m570_scaled_bc_public_natural_surface_eval_aggregate/summary.json
- parent_config: configs/ppo_m541_matched_l0_variance_4096.json, configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: design moderate-OOD route/generalization profile after M572 fresh route pass
- derived_from: m572-fresh-route-generalization-eval
- blocked_by: m572-fresh-route-generalization-eval
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies eval-only L0 L2 and L3 config deltas for moderate OOD route evaluation
- design specifies fresh OOD seed range and scenario count
- design specifies BC5660 versus L0/L2 pass/fail criteria before evaluation
- design keeps actor inputs and checkpoint weights unchanged
- research validation passes

## Failure Criteria

- design changes actor inputs or L2/L3 history contract
- design uses public frozen-source rows or prior route seeds as OOD evidence
- design allows training or promotion before OOD results exist

## Evidence Gates

- design eval-only moderate-OOD route configs for L0 L2 and BC5660
- widen speed friction obstacle and hidden-vehicle randomization without changing actor inputs
- pre-register fresh OOD seed range and pass/fail criteria
- do not train or promote in design milestone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune from M572 failures before reporting M573 design
- do not reuse route-screen seeds 15560 16560 17560 18560 or 19560
- do not use public frozen-source natural-surface rows
- do not run PPO or behavior cloning
- do not change the P0 human-view no-wheel no-oracle actor contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m573-moderate-ood-route-generalization-design
- type: infrastructure
- checkpoint: docs/m573-moderate-ood-route-generalization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: moderate_ood_route_design_admit_m574_config_family
- reason: M573 pre-registers eval-only moderate-OOD config deltas seed range 20560..20815 and relaxed L2 competitiveness tolerances before any OOD eval

## Next Blocker

m574-moderate-ood-config-family
