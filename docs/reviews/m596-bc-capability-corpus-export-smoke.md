# m596-bc-capability-corpus-export-smoke Research Review

## Summary

- Generated at UTC: 20260524T074156Z
- Type: gate
- Gate tier: infrastructure
- Promotion decision: bc_capability_corpus_export_smoke_admit_repair_smoke_design
- Decision reason: M596 exports train and validation capability corpora with 112/58 rows and 240/240 pair rows while preserving P0 actor inputs and keeping labels as targets only

## Hypothesis

The M595 corpus runner can export separate train and validation capability corpora with non-empty same-corpus pair rows, preserving P0 actor inputs and producing enough data for a later objective smoke.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m595_bc_capability_corpus_pair_smoke/summary.json
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: export train and validation capability corpora before repair optimizer smoke
- derived_from: m595-bc-capability-corpus-runner-implementation
- blocked_by: m595-bc-capability-corpus-runner-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- train and validation summary.json files exist
- both corpora have student_obs_dim 72 action_dim 3 target_dim 3
- both corpora report labels_enter_actor_input false
- both pair counts are non-zero
- research validation and focused tests pass

## Failure Criteria

- any corpus has zero rows
- any corpus has zero pair rows
- actor observation dim differs from 72
- capability labels enter actor inputs
- a checkpoint is trained or promoted

## Evidence Gates

- export train capability corpus
- export validation capability corpus
- verify pair rows and target summaries are non-empty
- verify labels remain targets only and actor observation dim is 72

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train repair model
- do not run PPO
- do not promote checkpoint
- do not add capability labels or hidden physical parameters to actor observations
- do not claim driver performance from corpus export

## Failure Taxonomy

- none

## Scoreboard

- milestone: m596-bc-capability-corpus-export-smoke
- type: gate
- checkpoint: runs/m596_bc_capability_corpus_train_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_capability_corpus_export_smoke_admit_repair_smoke_design
- reason: M596 exports train and validation capability corpora with 112/58 rows and 240/240 pair rows while preserving P0 actor inputs and keeping labels as targets only

## Next Blocker

m597-bc-capability-repair-objective-smoke-design
