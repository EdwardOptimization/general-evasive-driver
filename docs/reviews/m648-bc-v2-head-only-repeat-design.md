# m648-bc-v2-head-only-repeat-design Research Review

## Summary

- Generated at UTC: 20260524T125817Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bc_v2_head_only_repeat_design_admit_m649
- Decision reason: M648 designs a three-seed best-validation frozen-head repeat with actor checksum gates wrong-history summaries and no actor coupling

## Hypothesis

A best-validation multi-seed frozen-head repeat can preserve the M646 learnability result while controlling head-level overfit before any actor-coupling design.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m646_bc_v2_head_only_smoke/summary.json, runs/m646_bc_v2_head_only_smoke/validation_metrics.csv, docs/m647-bc-v2-head-only-smoke-audit.md
- parent_config: experiments/manifests/m647-bc-v2-head-only-smoke-audit.json
- parent_objective: design an early-stopped multi-seed frozen-actor head-only repeat after M646 validation overfit
- derived_from: m647-bc-v2-head-only-smoke-audit
- blocked_by: m647-bc-v2-head-only-smoke-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies seeds and early-stopping rule
- design specifies best-validation head artifact
- design preserves actor checksum gate
- design includes wrong-history source audit
- research validation passes

## Failure Criteria

- design allows actor coupling
- design omits best-validation selection
- design omits multi-seed repeat
- design treats head-only result as promotion evidence

## Evidence Gates

- design multi-seed frozen-head repeat
- save best validation head rather than final epoch only
- preserve source-balanced masked losses
- verify actor checksum unchanged for every seed
- keep actor coupling and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in design milestone
- do not update actor parameters in later repeat
- do not promote checkpoint
- do not treat source-heldout as private evidence
- do not ignore wrong-history source weakness

## Failure Taxonomy

- none

## Scoreboard

- milestone: m648-bc-v2-head-only-repeat-design
- type: infrastructure
- checkpoint: docs/m648-bc-v2-head-only-repeat-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_v2_head_only_repeat_design_admit_m649
- reason: M648 designs a three-seed best-validation frozen-head repeat with actor checksum gates wrong-history summaries and no actor coupling

## Next Blocker

m649-bc-v2-head-only-repeat-implementation
