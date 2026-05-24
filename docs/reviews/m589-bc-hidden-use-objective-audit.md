# m589-bc-hidden-use-objective-audit Research Review

## Summary

- Generated at UTC: 20260524T071507Z
- Type: gate
- Gate tier: process
- Promotion decision: bc_hidden_use_objective_audit_admit_sensitivity_probe
- Decision reason: M589 finds the online-GRU actor has a structural hidden-to-action path but the scaled BC objective is one-step teacher-action MSE and does not force hidden-state self-ID; M590 sensitivity probe design admitted

## Hypothesis

The scaled L3 BC objective likely copied L2 route behavior through current response and previous-command features without creating causal hidden-to-action dependence; M589 should verify the objective and identify a repair path.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m567_scaled_l2_teacher_corpus_train/l2_teacher_corpus.npz, runs/m567_scaled_l2_teacher_corpus_validation/l2_teacher_corpus.npz, runs/m587_bc5660_history_action_screen_fresh_seed25560/variant_summary.csv, runs/m587_bc5660_history_action_screen_ood_seed25660/variant_summary.csv
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: audit why scaled L3 BC transfers behavior without wrong/delayed hidden-action sensitivity
- derived_from: m588-bc5660-history-action-screen-negative-audit
- blocked_by: m588-bc5660-history-action-screen-negative-audit
- supersedes: None
- invalidates: None

## Success Criteria

- audit documents the BC recurrent training path and its one-step teacher-action loss
- audit identifies whether existing code can measure hidden-to-action sensitivity or needs a small probe
- audit identifies whether the BC corpus has matched-current teacher-action ambiguity
- audit pre-registers the next concrete repair or probe milestone without training
- research validation passes

## Failure Criteria

- audit starts repair training before documenting the objective gap
- audit treats M587 negative result as a runtime error without evidence
- audit adds actor inputs or oracle targets
- audit promotes a checkpoint

## Evidence Gates

- inspect L3 BC objective and recurrent training path
- audit whether hidden state has a structural and empirical action path in BC5660
- audit whether the BC corpus creates matched-current history ambiguity for teacher actions
- select a repair direction without training or promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train or run PPO
- do not promote checkpoint
- do not add hidden vehicle parameters to actor inputs
- do not claim self-ID from route performance or zero-current sensitivity
- do not change the BC objective before the audit is documented

## Failure Taxonomy

- none

## Scoreboard

- milestone: m589-bc-hidden-use-objective-audit
- type: gate
- checkpoint: docs/m589-bc-hidden-use-objective-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_hidden_use_objective_audit_admit_sensitivity_probe
- reason: M589 finds the online-GRU actor has a structural hidden-to-action path but the scaled BC objective is one-step teacher-action MSE and does not force hidden-state self-ID; M590 sensitivity probe design admitted

## Next Blocker

m590-bc-hidden-action-sensitivity-probe-design
