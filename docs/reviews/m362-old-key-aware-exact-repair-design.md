# m362-old-key-aware-exact-repair-design Research Review

## Summary

- Generated at UTC: 20260523T112711Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: admit_m363_old_key_aware_repair_implementation
- Decision reason: M362 designs old-key-aware exact repair using an old-key preference corpus and optional surrogate loss while keeping closed-loop old-key replay as the outer proof gate

## Hypothesis

The M356/M358 failure mode can be addressed by designing exact repair/projection that treats old-key neighborhood proof as a first-class residual or constraint instead of relying on post-hoc interpolation after exact M297/M270.

## Lineage

- parent_checkpoint: runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt, runs/m356_m354_repair_best_step_probe/candidate_checkpoint.pt
- parent_dataset: docs/m361-micro-alpha-utility-audit.md, runs/m358_m354_best_step_old_key_micro_a00025_gate/summary.json, runs/m358_m354_best_step_old_key_micro_a0005_gate/summary.json, runs/m357_m354_best_step_proof_gate/summary.json
- parent_config: experiments/manifests/m361-micro-alpha-utility-audit.json
- parent_objective: design old-key-aware exact repair/projection before further PPO
- derived_from: m361-micro-alpha-utility-audit
- blocked_by: m361-micro-alpha-utility-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies the repair objective terms and lexicographic acceptance order
- design states how old-key neighborhood rows enter the repair or projection
- design states how to reject negligible-alpha directions
- next implementation milestone is registered
- research validation passes

## Failure Criteria

- design defers the old-key proof conflict to post-hoc promotion gates only
- design starts PPO before the repair objective is specified
- actor input contract changes
- research validation fails

## Evidence Gates

- process design only; no PPO run
- preserve exact M297/M270 as lexicographic no-regression objectives
- make old-key neighborhood proof first-class in the repair/projection design
- include source-diverse protected proof and first replay gates in acceptance order
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in the design milestone
- do not accept alpha clipping to 0.00025 as a solved training recipe
- do not remove old-key neighborhood proof from the acceptance stack
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m362-old-key-aware-exact-repair-design
- type: infrastructure
- checkpoint: runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m363_old_key_aware_repair_implementation
- reason: M362 designs old-key-aware exact repair using an old-key preference corpus and optional surrogate loss while keeping closed-loop old-key replay as the outer proof gate

## Next Blocker

m363-old-key-aware-repair-implementation
