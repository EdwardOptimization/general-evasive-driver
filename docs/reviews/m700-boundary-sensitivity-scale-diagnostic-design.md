# m700-boundary-sensitivity-scale-diagnostic-design Research Review

## Summary

- Generated at UTC: 20260524T170504Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: boundary_sensitivity_scale_diagnostic_design_admit_m701
- Decision reason: M700 designs a no-training window and perturbation-scale ladder with plausible stress and unrealistic classes before any objective actor update PPO or promotion

## Hypothesis

A registered window and perturbation-scale diagnostic can determine whether M698 was empty because the perturbations/window were too conservative or because the base-policy distribution lacks local terminal-boundary sensitivity.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m699-fresh-trajectory-boundary-sampler-audit.md, runs/m698_fresh_trajectory_boundary_sampler/summary.json, runs/m698_fresh_trajectory_boundary_sampler/prepass_rows.csv, runs/m698_fresh_trajectory_boundary_sampler/rejected_rows.csv
- parent_config: experiments/manifests/m699-fresh-trajectory-boundary-sampler-audit.json
- parent_objective: design perturbation-scale and window diagnostic for fresh boundary sampling
- derived_from: m699-fresh-trajectory-boundary-sampler-audit
- blocked_by: m699-fresh-trajectory-boundary-sampler-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design defines target-obstacle-distance variants
- design defines max-prepass-margin variants
- design defines plausible and stress perturbation scales
- design defines per-scale acceptance and rejection metrics
- design defines negative-result interpretation
- objective actor update PPO and promotion remain blocked

## Failure Criteria

- design only loosens thresholds without scale reporting
- design admits objective training before source-positive evidence
- design omits normal-failed or too-safe accounting
- design omits perturbation realism boundaries
- design changes actor input contract

## Evidence Gates

- design compares perturbation scales before objective design
- design compares snapshot/window targets before objective design
- design reports normal-failed too-safe and sensitivity ratios
- design blocks actor update PPO and promotion
- design preserves P0 actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor
- do not run PPO
- do not promote a checkpoint
- do not call large action overrides a deployable policy
- do not accept threshold loosening as source-positive without scale diagnostics
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m700-boundary-sensitivity-scale-diagnostic-design
- type: infrastructure
- checkpoint: docs/m700-boundary-sensitivity-scale-diagnostic-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: boundary_sensitivity_scale_diagnostic_design_admit_m701
- reason: M700 designs a no-training window and perturbation-scale ladder with plausible stress and unrealistic classes before any objective actor update PPO or promotion

## Next Blocker

m701-boundary-sensitivity-scale-diagnostic-implementation
