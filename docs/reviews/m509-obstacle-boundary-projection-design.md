# m509-obstacle-boundary-projection-design Research Review

## Summary

- Generated at UTC: 20260524T010714Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m510_obstacle_boundary_projection_miner
- Decision reason: M509 designs bounded obstacle-boundary projection from M508 natural anchors as labelled projection proof with projection magnitude limits and no actor contract change

## Hypothesis

Because M508 has many low-clearance anchors and action signal but few source-capped natural geometry buckets, bounded obstacle projection around natural anchors is the next admissible diagnostic proof path.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m508_terminal_boundary_anchor_miner/summary.json, runs/m508_terminal_boundary_anchor_miner/anchors.csv, runs/m508_terminal_boundary_anchor_miner/scored_pairs.csv, runs/m508_terminal_boundary_anchor_miner/targeted_pairs.csv
- parent_config: configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json, configs/m502_natural_boundary_pressure_warmup_zero_relvel.json, experiments/manifests/m508-terminal-boundary-anchor-miner.json
- parent_objective: obstacle-boundary projection proof design
- derived_from: m508-terminal-boundary-anchor-miner
- blocked_by: m508-terminal-boundary-anchor-miner
- supersedes: None
- invalidates: None

## Success Criteria

- classify the M508 failure as geometry/label concentration rather than absence of action signal
- define projection metadata and geometry-change constraints
- define source-diversity and projection-magnitude admission gates
- state that projected rows are projection proof, not raw natural proof
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- design relaxes M508 caps after seeing the result
- design claims projection rows as raw natural proof
- design changes ego state or hidden dynamics instead of obstacle geometry
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- diagnose why M508 anchor-first mining still fails source-capped admission
- define obstacle-boundary projection as explicitly labelled projection proof
- define projection magnitude metadata and admission limits
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not use hidden-hold variants as deployable proof
- do not claim projected rows as raw natural proof
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m509-obstacle-boundary-projection-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m510_obstacle_boundary_projection_miner
- reason: M509 designs bounded obstacle-boundary projection from M508 natural anchors as labelled projection proof with projection magnitude limits and no actor contract change

## Next Blocker

M510 should implement bounded obstacle-boundary projection mining before any outcome gate.
