# m443-active-boundary-v2-stop-audit Research Review

## Summary

- Generated at UTC: 20260523T191537Z
- Type: gate
- Gate tier: process
- Promotion decision: stop_active_boundary_v2_branch_admit_generalization_audit
- Decision reason: M443 stops active-boundary v2 after repeated old-key proof utility bottleneck and admits a non-promotion broad benchmark audit

## Hypothesis

The active-boundary residual branch has reached a repeated proof/utility bottleneck and should be closed before choosing the next research direction.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m438_r0015_active_boundary_lactive1e12_s40_seed10161/candidate_checkpoint.pt, runs/m442_tail_r0010_active_boundary_v2_l1e12_s40_seed10162/candidate_checkpoint.pt
- parent_dataset: runs/m437_active_boundary_residual/active_boundary_corpus.npz, runs/m441_active_boundary_v2_residual/active_boundary_v2_corpus.npz, runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv
- parent_config: experiments/manifests/m436-old-key-active-boundary-residual-design.json, experiments/manifests/m440-active-boundary-v2-residual-design.json, experiments/manifests/m442-active-boundary-v2-projection-probe.json
- parent_objective: active-boundary v1 and v2 no-PPO proof/utility probes
- derived_from: m442-active-boundary-v2-projection-probe
- blocked_by: m442-active-boundary-v2-projection-probe
- supersedes: None
- invalidates: None

## Success Criteria

- classify whether active-boundary v2 should stop or continue
- identify the binding failure rows and utility ceiling
- choose a next milestone that is not another scalar active-boundary sweep
- keep the current public-gate base unchanged

## Failure Criteria

- recommends more active-boundary scalar tuning without new evidence
- treats exact residual metrics as promotion evidence despite closed-loop replay failure
- changes actor input/output contract
- claims driver improvement from a rejected candidate

## Evidence Gates

- M438 proof-safe r0015 recovery retained 0.120957
- M442 v2 tail old-key compact 39 of 40
- M442 recovery retained 0.111895
- M267/M264 and M183/M170 first replay pass

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not run another active-boundary scalar sweep
- do not lower old-key compact thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- protected_key_window_failure
- objective_overfit

## Scoreboard

- milestone: m443-active-boundary-v2-stop-audit
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: stop_active_boundary_v2_branch_admit_generalization_audit
- reason: M443 stops active-boundary v2 after repeated old-key proof utility bottleneck and admits a non-promotion broad benchmark audit

## Next Blocker

m444-proof-utility-generalization-audit
