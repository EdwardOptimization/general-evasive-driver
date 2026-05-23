# m361-micro-alpha-utility-audit Research Review

## Summary

- Generated at UTC: 20260523T112411Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_m362_old_key_aware_exact_repair_design
- Decision reason: M361 classifies M360 alpha 0.00025 as a proof-safe micro-step rather than meaningful driver improvement; next step is old-key-aware exact repair design before more PPO

## Hypothesis

Although M360 promotes alpha 0.00025, the movement may be too small to justify another PPO chain; a process audit should decide the next research direction before further training.

## Lineage

- parent_checkpoint: runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt, runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
- parent_dataset: runs/m360_full_public_gate_for_m358_a00025/summary.json, docs/m360-full-public-gate-for-m358-a00025.md
- parent_config: experiments/manifests/m360-full-public-gate-for-m358-a00025.json, docs/m360-full-public-gate-for-m358-a00025.md
- parent_objective: audit whether the promoted micro-alpha is meaningful enough to chain PPO from
- derived_from: m360-full-public-gate-for-m358-a00025
- blocked_by: m360-full-public-gate-for-m358-a00025
- supersedes: None
- invalidates: None

## Success Criteria

- audit states whether alpha 0.00025 is meaningful progress or only retention
- audit recommends the next blocker explicitly
- audit does not run PPO
- research validation passes

## Failure Criteria

- audit ignores the micro-alpha limitation
- audit starts PPO before deciding whether the branch is useful
- actor input contract changes
- research validation fails

## Evidence Gates

- process audit only; no PPO run
- quantify exact-objective movement from M352 to M358 alpha 0.00025
- quantify accepted alpha versus first failing alpha
- decide whether to chain PPO, redesign repair objective, or refresh proof surfaces
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat micro-alpha promotion as meaningful driver improvement without evidence
- do not start longer PPO before deciding whether this branch has usable movement
- do not change actor inputs
- do not hide the alpha 0.00025 limitation

## Failure Taxonomy

- none

## Scoreboard

- milestone: m361-micro-alpha-utility-audit
- type: gate
- checkpoint: runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m362_old_key_aware_exact_repair_design
- reason: M361 classifies M360 alpha 0.00025 as a proof-safe micro-step rather than meaningful driver improvement; next step is old-key-aware exact repair design before more PPO

## Next Blocker

m362-old-key-aware-exact-repair-design
