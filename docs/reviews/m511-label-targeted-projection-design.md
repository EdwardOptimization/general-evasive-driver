# m511-label-targeted-projection-design Research Review

## Summary

- Generated at UTC: 20260524T011751Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m512_label_targeted_projection_miner
- Decision reason: M511 designs label-targeted projection mining with projected-label diversity and geometry magnitude limits while keeping projected labels out of actor inputs

## Hypothesis

M510 fails because small local obstacle projections do not cross scenario-label boundaries, so a label-targeted projection miner is needed for a source-diverse projection-proof surface.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m510_obstacle_boundary_projection_miner/summary.json, runs/m510_obstacle_boundary_projection_miner/scored_pairs.csv, runs/m510_obstacle_boundary_projection_miner/targeted_pairs.csv
- parent_config: configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json, configs/m502_natural_boundary_pressure_warmup_zero_relvel.json, experiments/manifests/m510-obstacle-boundary-projection-miner.json
- parent_objective: label-targeted projection proof design
- derived_from: m510-obstacle-boundary-projection-miner
- blocked_by: m510-obstacle-boundary-projection-miner
- supersedes: None
- invalidates: None

## Success Criteria

- classify the M510 failure as label degeneracy rather than action-signal absence
- define target projected labels and candidate geometry grid
- define projection magnitude and half-width change limits
- state that projected labels are offline mining metadata only
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- design relaxes M510 label diversity after seeing the result
- design uses projected label as actor input
- design changes ego state or hidden dynamics
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- diagnose why M510 projected rows remain label-degenerate
- define label-targeted projection families and metadata
- define source-diversity and projection-magnitude admission gates
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not use hidden-hold variants as deployable proof
- do not claim projected rows as raw natural proof
- do not relax projected-label diversity after seeing M510

## Failure Taxonomy

- none

## Scoreboard

- milestone: m511-label-targeted-projection-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m512_label_targeted_projection_miner
- reason: M511 designs label-targeted projection mining with projected-label diversity and geometry magnitude limits while keeping projected labels out of actor inputs

## Next Blocker

M512 should implement label-targeted projection mining before any outcome gate.
