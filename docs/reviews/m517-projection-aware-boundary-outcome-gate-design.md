# m517-projection-aware-boundary-outcome-gate-design Research Review

## Summary

- Generated at UTC: 20260524T020000Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m518_projection_aware_boundary_outcome_gate
- Decision reason: M517 designs a projection-aware outcome gate that preserves relocated obstacle geometry and classifies positive proof margin-only signal control-only sensitivity fast correction or invalid replay

## Hypothesis

A valid downstream outcome gate for M516 must be projection-aware because old tail-aligned replay would reconstruct original obstacle geometry and lose the projected terminal-boundary proof surface.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m516_boundary_mechanism_projection_selector/targeted_pairs.csv, runs/m516_boundary_mechanism_projection_selector/summary.json
- parent_config: configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json, configs/m502_natural_boundary_pressure_warmup_zero_relvel.json, experiments/manifests/m516-boundary-mechanism-projection-selector.json
- parent_objective: projection-aware boundary outcome gate design
- derived_from: m516-boundary-mechanism-projection-selector
- blocked_by: m516-boundary-mechanism-projection-selector
- supersedes: None
- invalidates: None

## Success Criteria

- define projection-aware replay semantics
- define variants and offsets
- define metrics and result classifications
- define how wrong-history proof differs from reset and zero-current controls
- record the relation to L3 recurrent belief policy evidence
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- design reuses original-geometry replay for projected rows
- design uses projected labels as actor inputs
- design conflates wrong-history and reset or zero-current controls
- design treats fast correction as a policy failure without evidence
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- design an outcome gate that preserves M516 relocated obstacle geometry
- separate wrong-history rows from reset and zero-current controls
- pre-register result classifications including fast-correction no-effect
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not replay original obstacle geometry for projected rows
- do not treat scenario labels as actor inputs
- do not treat fast correction as policy failure without evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m517-projection-aware-boundary-outcome-gate-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m518_projection_aware_boundary_outcome_gate
- reason: M517 designs a projection-aware outcome gate that preserves relocated obstacle geometry and classifies positive proof margin-only signal control-only sensitivity fast correction or invalid replay

## Next Blocker

M518 should implement and run the projection-aware boundary outcome gate.
