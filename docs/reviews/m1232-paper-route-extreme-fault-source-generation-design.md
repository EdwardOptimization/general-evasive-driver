# m1232-paper-route-extreme-fault-source-generation-design Research Review

## Summary

- Generated at UTC: 20260528T082311Z
- Type: gate
- Gate tier: process
- Promotion decision: extreme_fault_source_generation_design_admit_smoke
- Decision reason: M1232 defines current-model/proxy versus future high-fidelity fault families actor-input guardrails source-mining artifacts and source-diversity gates and admits bounded no-training M1233 smoke

## Hypothesis

A source-generation branch focused on hidden extreme/fault dynamics is higher leverage than continued grid tuning around M1230's source-collapsed short-horizon active set.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: runs/m1230_short_horizon_relocation_smoke/summary.json, docs/m1231-paper-route-short-horizon-partial-positive-audit.md
- parent_config: experiments/manifests/m1231-paper-route-short-horizon-partial-positive-audit.json
- parent_objective: design source-diverse extreme/fault scenario generation after M1230 partial-positive source collapse
- derived_from: m1231-paper-route-short-horizon-partial-positive-audit
- blocked_by: M1230 accepted rows are short-horizon and source-collapsed
- supersedes: continuing to tune the same M1226 public source pool
- invalidates: training directly from M1230 accepted rows

## Success Criteria

- docs/m1232-paper-route-extreme-fault-source-generation-design.md exists
- scenario families and hidden ranges are specified
- actor-input guardrails are specified
- source-diversity gates are specified
- first bounded implementation step is selected
- private holdout remains unused
- no training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs

## Failure Criteria

- M1232 trains or tunes profiles
- private holdout is used
- fault labels are added to actor inputs
- scenario design becomes too broad to validate
- next route is left vague

## Evidence Gates

- M1232 may design source-generation infrastructure only
- M1232 must preserve actor input contract
- M1232 must not train controllers
- M1232 must not run PPO
- M1232 must not use private holdout
- M1232 must not promote
- M1232 must keep hidden fault labels out of deployable actor inputs
- M1232 must select a bounded first implementation step

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add fault labels or hidden parameters to actor inputs
- do not treat fault scenario labels as oracle feasibility labels
- do not claim self-identification from scenario design

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1232-paper-route-extreme-fault-source-generation-design
- type: gate
- checkpoint: docs/m1232-paper-route-extreme-fault-source-generation-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: extreme_fault_source_generation_design_admit_smoke
- reason: M1232 defines current-model/proxy versus future high-fidelity fault families actor-input guardrails source-mining artifacts and source-diversity gates and admits bounded no-training M1233 smoke

## Next Blocker

m1233-paper-route-extreme-fault-source-smoke
