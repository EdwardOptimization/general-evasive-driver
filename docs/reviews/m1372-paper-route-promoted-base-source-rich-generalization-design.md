# m1372-paper-route-promoted-base-source-rich-generalization-design Research Review

## Summary

- Generated at UTC: 20260528T212208Z
- Type: gate
- Gate tier: process
- Promotion decision: promoted_base_source_rich_generalization_design_admit_smoke
- Decision reason: M1372 designs the no-training promoted-base source-rich public smoke with proxy claim boundaries and fixed L0-L3 ordering

## Hypothesis

A promoted-base source-rich public generalization gate can be designed without private holdout, proxy-physics overclaiming, or PPO.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1371-paper-route-post-public-base-promotion-synthesis.md, docs/m1370-paper-route-public-base-promotion-audit.md, configs/extreme_fault_distribution_v4_scenarios.json, configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
- parent_config: experiments/manifests/m1371-paper-route-post-public-base-promotion-synthesis.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: design source-rich public generalization gate for the promoted M1362 public base
- derived_from: m1371-paper-route-post-public-base-promotion-synthesis
- blocked_by: M1371 opens the promoted-base source-rich/comparison readiness branch
- supersedes: running source-rich evaluation without a promoted-base gate design, using private holdout for source-rich debugging, claiming true per-wheel asymmetric faults from current single-track proxy configs
- invalidates: None

## Success Criteria

- docs/m1372-paper-route-promoted-base-source-rich-generalization-design.md exists
- design specifies source-rich public distributions, metrics, and pass/fail criteria
- design specifies current-model fault versus proxy/future-only claim boundary
- design specifies how L0/L1/L2/L3 comparison is ordered relative to source-rich validation
- no training, PPO, evaluation, private holdout, actor update, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design omits fault claim boundary
- design uses private holdout for debugging
- design claims high-fidelity or paper-level source-rich evidence without a run
- training, PPO, evaluation, private holdout, actor update, or actor-input expansion occurs

## Evidence Gates

- M1372 must design source-rich public generalization for the promoted M1362 base
- M1372 must separate current-model faults from proxy/future-only high-fidelity faults
- M1372 must keep private holdout unused
- M1372 must not train, run PPO, run evaluation, or change actor inputs
- M1372 must keep L0/L1/L2/L3 comparison and source-rich gate ordering explicit

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run source-rich evaluation in the design milestone
- do not use private holdout
- do not add actor inputs
- do not claim true single-wheel, split-mu, halfshaft, or suspension physics from proxy configs
- do not claim paper-level evidence or level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1372-paper-route-promoted-base-source-rich-generalization-design
- type: gate
- checkpoint: docs/m1372-paper-route-promoted-base-source-rich-generalization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promoted_base_source_rich_generalization_design_admit_smoke
- reason: M1372 designs the no-training promoted-base source-rich public smoke with proxy claim boundaries and fixed L0-L3 ordering

## Next Blocker

m1373-paper-route-promoted-base-source-rich-smoke
