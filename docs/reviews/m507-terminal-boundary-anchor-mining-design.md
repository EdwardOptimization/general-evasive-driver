# m507-terminal-boundary-anchor-mining-design Research Review

## Summary

- Generated at UTC: 20260524T004844Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m508_terminal_boundary_anchor_miner
- Decision reason: M507 chooses anchor-first mining of low-clearance normal-history states and reserves obstacle-boundary projection as fallback if natural anchors fail

## Hypothesis

The next candidate pool must be mined from low-clearance normal-history anchors first, then paired with adversarial wrong histories; selecting from the existing M504 pair table is too source-capped.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m506_terminal_boundary_aware_selector/summary.json, runs/m506_terminal_boundary_aware_selector/terminal_boundary_candidates.csv, runs/m506_terminal_boundary_aware_selector/targeted_pairs.csv
- parent_config: configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json, configs/m502_natural_boundary_pressure_warmup_zero_relvel.json, experiments/manifests/m506-terminal-boundary-aware-selector.json
- parent_objective: terminal-boundary anchor mining design
- derived_from: m506-terminal-boundary-aware-selector
- blocked_by: m506-terminal-boundary-aware-selector
- supersedes: None
- invalidates: None

## Success Criteria

- classify whether M506 failed from candidate scarcity, caps, or label imbalance
- select a concrete anchor-mining implementation path
- define source-diversity and geometry/boundary admission thresholds
- state fallback if anchor mining still cannot find enough wrong-history action perturbations
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- design repeats M506 selector unchanged
- design admits outcome gate on M506 rows
- design uses persistent wrong hidden as deployable proof
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- diagnose why M506 remains source-capped and small
- design terminal-boundary anchor mining that starts from low-clearance normal-history states
- define how to search wrong histories around those anchors without hidden-hold forcing
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not use hidden-hold variants as deployable proof
- do not relax source caps after seeing M506
- do not run an outcome gate on M506's 101-row surface
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m507-terminal-boundary-anchor-mining-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m508_terminal_boundary_anchor_miner
- reason: M507 chooses anchor-first mining of low-clearance normal-history states and reserves obstacle-boundary projection as fallback if natural anchors fail

## Next Blocker

M508 should implement terminal-boundary anchor mining before any outcome gate.
