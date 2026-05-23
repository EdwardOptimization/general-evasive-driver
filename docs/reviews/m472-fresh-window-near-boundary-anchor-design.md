# m472-fresh-window-near-boundary-anchor-design Research Review

## Summary

- Generated at UTC: 20260523T214109Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: admit_m473_fresh_window_anchor_discovery_run
- Decision reason: M472 classifies M471 as count-pass balance-fail and designs fresh-window near-boundary anchor discovery before any adversarial outcome probe

## Hypothesis

M471 shows the same seed window can meet pair count but not seed balance; fresh windows need their own near-boundary anchor discovery before combining adversarial surfaces.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m471_expanded_adversarial_wrong_history_search/summary.json, runs/m471_expanded_adversarial_wrong_history_search/adversarial_pairs.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m471-expanded-adversarial-pool-run.json
- parent_objective: fresh-window near-boundary anchor discovery design
- derived_from: m471-expanded-adversarial-pool-run
- blocked_by: m471-expanded-adversarial-pool-run
- supersedes: None
- invalidates: None

## Success Criteria

- document M471 count-pass balance-fail result
- select a concrete fresh-window anchor discovery path
- define expected artifacts and pass/fail criteria
- preserve no-privileged-input actor contract
- no checkpoint is promoted

## Failure Criteria

- design proposes outcome probing on M471's imbalanced surface
- design relaxes seed-balance requirements
- design requires privileged actor inputs
- design proposes PPO before proof evidence

## Evidence Gates

- analyze why M471 count passes but seed balance fails
- design fresh-window near-boundary anchor discovery
- preserve P0 actor contract and normal-margin proof requirements
- pre-register the next implementation and pass/fail criteria
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not outcome-probe M471's imbalanced surface
- do not loosen single-seed cap
- do not add privileged actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m472-fresh-window-near-boundary-anchor-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m473_fresh_window_anchor_discovery_run
- reason: M472 classifies M471 as count-pass balance-fail and designs fresh-window near-boundary anchor discovery before any adversarial outcome probe

## Next Blocker

m473-fresh-window-anchor-discovery-run
