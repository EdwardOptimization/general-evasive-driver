# m1666-paper-route-fusion-actor-artifact-replay-first-check Research Review

## Summary

- Generated at UTC: 20260529T221843Z
- Type: gate
- Gate tier: proof
- Promotion decision: fusion_actor_artifact_first_check_failed_route_to_audit
- Decision reason: M1666 checkpoint sanity passes but M183/M170 and M267/M264 first checks fail from normal-history behavior regression and proof retention loss

## Hypothesis

The M1663 artifact can pass checkpoint sanity and the first M183/M170 plus M267/M264 public proof replay checks before full-stack replay is considered.

## Lineage

- parent_checkpoint: runs/m1663_fusion_actor_checkpoint_artifact/checkpoints/alpha_0_2_fusion_actor_repaired.pt
- parent_dataset: docs/m1665-paper-route-fusion-actor-artifact-replay-gate-design.md, runs/m1663_fusion_actor_checkpoint_artifact/summary.json, runs/m1663_fusion_actor_checkpoint_artifact/artifact_metadata.json, runs/m1663_fusion_actor_checkpoint_artifact/checksums.sha256
- parent_config: experiments/manifests/m1665-paper-route-fusion-actor-artifact-replay-gate-design.json
- parent_objective: run checkpoint sanity and first public proof replay checks for the M1663 artifact
- derived_from: m1665-paper-route-fusion-actor-artifact-replay-gate-design
- blocked_by: M1665 admits only Stage 0 and Stage 1 first-check replay; full-stack replay PPO promotion and private holdout remain blocked
- supersedes: direct full-stack replay after M1665, direct PPO after M1665, direct promotion after M1665, private holdout after M1665
- invalidates: None

## Success Criteria

- runs/m1666_fusion_actor_artifact_replay_first_check/summary.json exists
- checkpoint_sanity_pass is true
- m183_m170_first_check_pass is true
- m267_m264_first_check_pass is true
- first_check_pass is true
- full-stack replay PPO training promotion private holdout actor-input changes and level3 claims remain blocked
- M1667 audit manifest is created

## Failure Criteria

- checkpoint sanity fails
- P0 actor contract fails
- M183/M170 first-check fails
- M267/M264 first-check fails
- replay execution errors occur
- implementation runs full-stack replay PPO training promotion private holdout actor-input changes or claims level3 self-identification

## Evidence Gates

- M1666 must verify artifact checksum and metadata before replay
- M1666 must verify P0 human-view no-wheel actor contract
- M1666 must run M183/M170 first-check replay
- M1666 must run M267/M264 first-check replay
- M1666 must not run full-stack replay PPO training promotion private holdout actor-input changes or level3 claims
- M1666 must route to result audit regardless of pass or fail

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run full-stack replay
- do not run PPO
- do not train
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not rerun artifact materialization
- do not tune repair parameters
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- proof_washout
- behavior_regression

## Scoreboard

- milestone: m1666-paper-route-fusion-actor-artifact-replay-first-check
- type: gate
- checkpoint: runs/m1666_fusion_actor_artifact_replay_first_check/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: fusion_actor_artifact_first_check_failed_route_to_audit
- reason: M1666 checkpoint sanity passes but M183/M170 and M267/M264 first checks fail from normal-history behavior regression and proof retention loss

## Next Blocker

m1667-paper-route-fusion-actor-artifact-first-check-failure-audit
