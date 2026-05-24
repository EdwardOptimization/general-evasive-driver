# m545-l3-recurrent-recipe-repair-design Research Review

## Summary

- Generated at UTC: 20260524T040241Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: l3_recurrent_repair_design_admit_m546_config_family
- Decision reason: M545 defines controlled L3-only recurrent repair configs checkpoint-selection route-health gates and re-matching boundaries without training

## Hypothesis

The next step should repair recurrent optimization and checkpoint-selection discipline for L3 before more matched variance training, while preserving L2 as the finite-window baseline.

## Lineage

- parent_checkpoint: runs/m542_matched_l3_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m544_l3_variance_recipe_failure_audit/summary.json, runs/m543_m542_public_surface_eval_aggregate/summary.json
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/ppo_m541_matched_l2_variance_4096.json
- parent_objective: design L3 recurrent recipe repair after M543/M544 instability evidence
- derived_from: m544-l3-variance-recipe-failure-audit
- blocked_by: m544-l3-variance-recipe-failure-audit
- supersedes: None
- invalidates: None

## Success Criteria

- repair candidates are listed with allowed config changes
- route-health and public diagnostic gates are defined
- comparison back to L0/L2 is explicitly required after repair
- research validation passes

## Failure Criteria

- design allows unbounded per-level tuning without later re-matching
- design ignores M543/M544 L3 regression
- design treats public rows as private evidence

## Evidence Gates

- pre-register L3 repair candidates and diagnostic controls
- define checkpoint selection and route-health gates before public frozen-source eval
- preserve L2 as the finite-window baseline
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune L3 directly to M543 public rows and then claim private evidence
- do not discard L2 because the target is recurrent belief
- do not run repaired training before repair criteria are documented

## Failure Taxonomy

- training_instability

## Scoreboard

- milestone: m545-l3-recurrent-recipe-repair-design
- type: infrastructure
- checkpoint: docs/m545-l3-recurrent-recipe-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: l3_recurrent_repair_design_admit_m546_config_family
- reason: M545 defines controlled L3-only recurrent repair configs checkpoint-selection route-health gates and re-matching boundaries without training

## Next Blocker

m546-l3-recurrent-repair-config-family
