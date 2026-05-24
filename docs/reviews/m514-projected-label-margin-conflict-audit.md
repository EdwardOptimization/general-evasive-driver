# m514-projected-label-margin-conflict-audit Research Review

## Summary

- Generated at UTC: 20260524T014449Z
- Type: gate
- Gate tier: proof
- Promotion decision: confirm_label_margin_conflict_admit_m515_gate_split
- Decision reason: M514 scores 78490 projected candidates with 4 labels but low-margin non-unavoidable count is 0 and non-unavoidable min margin is 6.505553 so proof/scenario gate split is required

## Hypothesis

A broader diagnostic projection grid can determine whether M512's label-diversity failure is structural or merely a missing projection-family issue.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m512_label_targeted_projection_miner/summary.json, runs/m512_label_targeted_projection_miner/scored_pairs.csv
- parent_config: configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json, configs/m502_natural_boundary_pressure_warmup_zero_relvel.json, experiments/manifests/m513-projected-label-margin-conflict-design.json
- parent_objective: projected label-margin conflict audit
- derived_from: m513-projected-label-margin-conflict-design
- blocked_by: m513-projected-label-margin-conflict-design
- supersedes: None
- invalidates: None

## Success Criteria

- audit runs on M512/M508 source pairs and both M502 configs
- reports counts by projected label and normal-margin bucket
- reports projection magnitude and half-width delta buckets
- reports whether any non-unavoidable rows have normal_min_clearance_margin <= 2.0
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- audit admits an outcome gate directly
- audit changes actor inputs
- audit trains or promotes checkpoint

## Evidence Gates

- audit projected label versus normal-margin overlap under a broader diagnostic projection grid
- report whether low-margin non-unavoidable rows exist
- recommend either a new selector family or a pre-registered proof/scenario gate split
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not claim projected rows as raw natural proof
- do not use private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m514-projected-label-margin-conflict-audit
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: confirm_label_margin_conflict_admit_m515_gate_split
- reason: M514 scores 78490 projected candidates with 4 labels but low-margin non-unavoidable count is 0 and non-unavoidable min margin is 6.505553 so proof/scenario gate split is required

## Next Blocker

M515 should pre-register a proof/scenario gate split before another selector.
