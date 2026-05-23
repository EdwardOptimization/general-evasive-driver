# m470-expanded-adversarial-pool-design Research Review

## Summary

- Generated at UTC: 20260523T213008Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: admit_m471_expanded_adversarial_pool_run
- Decision reason: M470 designs expanded same-window matched-current mining before any outcome probe on adversarial pairs

## Hypothesis

M469 failed because the M462 full candidate pool is too small around near-boundary anchors; the next step should expand the mining pool before outcome probing.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m469_adversarial_wrong_history_pair_search/summary.json, runs/m469_adversarial_wrong_history_pair_search/adversarial_pairs.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m469-adversarial-wrong-history-pair-search.json
- parent_objective: expanded adversarial candidate-pool design
- derived_from: m469-adversarial-wrong-history-pair-search
- blocked_by: m469-adversarial-wrong-history-pair-search
- supersedes: None
- invalidates: None

## Success Criteria

- document the M469 pool-size and seed-balance failure
- select a concrete expanded-pool implementation path
- define expected artifacts and pass/fail criteria
- preserve no-privileged-input actor contract
- no checkpoint is promoted

## Failure Criteria

- design proposes outcome probing on the imbalanced M469 pool
- design skips near-boundary anchors
- design requires privileged actor inputs
- design proposes PPO before proof evidence

## Evidence Gates

- analyze why M469 pool coverage is too small and seed-imbalanced
- design a larger fresh adversarial-pair mining pool
- preserve P0 actor contract and near-boundary normal-margin requirement
- pre-register the next implementation and pass/fail criteria
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not run outcome probe on the imbalanced M469 surface
- do not loosen normal-margin requirements
- do not add privileged actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m470-expanded-adversarial-pool-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m471_expanded_adversarial_pool_run
- reason: M470 designs expanded same-window matched-current mining before any outcome probe on adversarial pairs

## Next Blocker

m471-expanded-adversarial-pool-run
