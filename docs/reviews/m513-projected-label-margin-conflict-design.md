# m513-projected-label-margin-conflict-design Research Review

## Summary

- Generated at UTC: 20260524T012956Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m514_projected_label_margin_conflict_audit
- Decision reason: M513 designs an audit to decide whether low-margin non-unavoidable projected rows are structurally absent before changing proof or scenario gate criteria

## Hypothesis

The M512 failure is a structural conflict between projected scenario labels and terminal-boundary low margins in the current M502 projection family, so an explicit label-margin conflict audit is needed before changing gates.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m512_label_targeted_projection_miner/summary.json, runs/m512_label_targeted_projection_miner/scored_pairs.csv, runs/m512_label_targeted_projection_miner/targeted_pairs.csv
- parent_config: configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json, configs/m502_natural_boundary_pressure_warmup_zero_relvel.json, experiments/manifests/m512-label-targeted-projection-miner.json
- parent_objective: projected label-margin conflict audit design
- derived_from: m512-label-targeted-projection-miner
- blocked_by: m512-label-targeted-projection-miner
- supersedes: None
- invalidates: None

## Success Criteria

- classify the M512 failure as label-margin non-overlap rather than absence of projected labels
- define a broader diagnostic projection grid
- define what evidence would justify a new selector
- define what evidence would justify splitting proof gates from scenario-distribution label gates
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- design relaxes M512 label diversity without an audit
- design uses projected label as actor input
- design admits outcome gate directly from M512
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- diagnose why M512 projected label diversity does not overlap terminal-boundary low margins
- define a broader audit grid for label/margin intersection
- define decision rules for selector continuation versus proof/scenario gate split
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not claim projected rows as raw natural proof
- do not relax M512 gates without a pre-registered replacement

## Failure Taxonomy

- none

## Scoreboard

- milestone: m513-projected-label-margin-conflict-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m514_projected_label_margin_conflict_audit
- reason: M513 designs an audit to decide whether low-margin non-unavoidable projected rows are structurally absent before changing proof or scenario gate criteria

## Next Blocker

M514 should audit whether low-margin non-unavoidable projected rows exist under broader diagnostic projection families.
