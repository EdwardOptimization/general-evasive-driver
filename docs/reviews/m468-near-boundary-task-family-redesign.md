# m468-near-boundary-task-family-redesign Research Review

## Summary

- Generated at UTC: 20260523T211926Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: admit_m469_adversarial_wrong_history_pair_search
- Decision reason: M468 selects adversarial right-history search over full candidate_pairs.csv anchored on M467 near-boundary left states

## Hypothesis

Because M467 found 35 near-boundary no-effect wrong-history rows and zero proof rows, the task family or wrong-history intervention must be redesigned rather than retuning selector thresholds.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m467_near_boundary_wrong_history_selector/summary.json, runs/m467_near_boundary_wrong_history_selector/near_boundary_no_effect.csv, runs/m467_near_boundary_wrong_history_selector/high_slack_diagnostics.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m467-near-boundary-wrong-history-selector.json
- parent_objective: near-boundary wrong-history task-family redesign
- derived_from: m467-near-boundary-wrong-history-selector
- blocked_by: m467-near-boundary-wrong-history-selector
- supersedes: None
- invalidates: None

## Success Criteria

- document the M467 no-effect failure mode
- select one concrete next implementation path
- define expected artifacts and pass/fail criteria
- preserve no-privileged-input actor contract
- no checkpoint is promoted

## Failure Criteria

- design treats high-slack diagnostics as proof
- design skips near-boundary normal-margin requirements
- design requires privileged actor inputs
- design proposes PPO before objective/gate sanity

## Evidence Gates

- analyze why M467 near-boundary rows show no wrong-history effect
- design a task-family or intervention change that can create low-margin wrong-history failures
- preserve the P0 actor contract
- pre-register the next implementation and pass/fail criteria
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not change actor input/output contract
- do not add hidden or oracle actor inputs
- do not loosen M467 by counting high-slack diagnostics as proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m468-near-boundary-task-family-redesign
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m469_adversarial_wrong_history_pair_search
- reason: M468 selects adversarial right-history search over full candidate_pairs.csv anchored on M467 near-boundary left states

## Next Blocker

m469-adversarial-wrong-history-pair-search
