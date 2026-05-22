# Current Status

This file is the compact official state for the project. Milestone documents
remain the detailed experiment log; this page should stay short and current.

## Project Identity

- Repository: `general-evasive-driver`
- Current Python package name: `autodrift`
- Working title: General Evasive Driver
- Core direction: closed-loop RL driver for handling-limit emergency avoidance,
  with drift as one possible maneuver rather than the project identity.

## Actor Contract

Mainline actor:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

Allowed deployable inputs:

- ego kinematics / IMU-like response;
- steering, throttle, and brake actuator state;
- previous physical commands;
- road / free-space / obstacle geometry in ego frame;
- recurrent state from past command-response history.

Not allowed in the deployable actor:

- `mu`, mass, CG, tire stiffness, brake scale, actuator time constants;
- slip ratio, slip angle, tire force, tire saturation, friction margin;
- AEB/AES/drift-required feasibility labels;
- controller mode or rule branch;
- `speed_ref`, `beta_target`, path error, heading error, path curvature;
- TTC, required clearance, oracle stopping distance, reference trajectory;
- collision/success/progress labels or any precomputed answer.

## Current Checkpoints

| Role | Checkpoint | Status |
| --- | --- | --- |
| strict anchor | `runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt` | strict full-replay anchor |
| split-aware candidate | `runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt` | preserves robust rows but loses knife-edge row 67 |
| guarded actor-update candidate | `runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt` | passes M183 objective, behavior, protected key, and M168/M170 boundary replay |
| guarded PPO smoke candidate | `runs/ppo_m185_guarded_from_m184_seed5185/checkpoint.pt` | positive single-seed PPO smoke; requires repeat before longer PPO |
| repeated PPO smoke candidates | `runs/ppo_m186_guarded_from_m184_seed5186/checkpoint.pt`, `runs/ppo_m186_guarded_from_m184_seed5187/checkpoint.pt` | preserve gates; fixed objective mixed, so M185 remains best fixed-loss candidate |
| guarded stage2 candidate | `runs/ppo_m187_stage2_from_m185_seed5190/checkpoint.pt` | positive single-seed stage2; requires repeat before longer PPO |
| repeated stage2 candidates | `runs/ppo_m188_stage2_from_m185_seed5191/checkpoint.pt`, `runs/ppo_m188_stage2_from_m185_seed5192/checkpoint.pt` | preserve gates; seed 5191 has current best fixed M183 loss |
| guarded stage3 candidate | `runs/ppo_m189_stage3_from_m188_seed5193/checkpoint.pt` | positive single-seed stage3; requires repeat before longer PPO |
| repeated stage3 candidates | `runs/ppo_m190_stage3_from_m188_seed5194/checkpoint.pt`, `runs/ppo_m190_stage3_from_m188_seed5195/checkpoint.pt` | preserve gates but do not beat M189 fixed loss |
| current-best actor-update candidate | `runs/m194_m189_actor_coupling_anchor100_s20_seed9850/optimized_checkpoint.pt` | best refreshed M193 fixed-objective actor update; seed-repeat stable |
| current-best guarded PPO smoke | `runs/ppo_m196_guarded_from_m194_seed5196/checkpoint.pt` | positive retention smoke from M194; requires repeat before longer PPO |
| current-best guarded PPO repeat | `runs/ppo_m197_guarded_from_m194_seed5197/checkpoint.pt` | best fixed-loss M197 repeat; preserves behavior, protected key, old replay, and refreshed replay |
| current-best guarded stage2 | `runs/ppo_m198_stage2_from_m197_seed5200/checkpoint.pt` | positive single-seed stage2; requires repeat before further continuation |
| current-best guarded stage2 repeat | `runs/ppo_m199_stage2_from_m197_seed5201/checkpoint.pt` | best fixed-loss M199 repeat; preserves behavior, protected key, old replay, and refreshed replay |
| current-best guarded stage3 | `runs/ppo_m200_stage3_from_m199_seed5203/checkpoint.pt` | positive single-seed stage3; smoke eval termination elevated; requires repeat before further continuation |
| current-best guarded stage3 repeat | `runs/ppo_m201_stage3_from_m199_seed5204/checkpoint.pt` | best fixed-loss M201 repeat; preserves behavior, protected key, old replay, and refreshed replay |
| current-best guarded stage4 | `runs/ppo_m202_stage4_from_m201_seed5206/checkpoint.pt` | positive single-seed stage4; requires repeat before further continuation |
| current-best guarded stage4 repeat evidence | `runs/ppo_m202_stage4_from_m201_seed5206/checkpoint.pt` | M203 repeats preserve gates, but M202 remains best fixed-loss stage4 |
| current-best guarded stage5 | `runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt` | positive single-seed stage5; requires repeat before further continuation |
| current-best guarded stage5 repeat evidence | `runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt` | M205 repeats preserve gates, but M204 remains best fixed-loss stage5 |

Do not replace M168 with M170 solely because M170 has better fixed objective or
slightly stronger action-level sensitivity.

## Current Evidence

- M177: action-level self-ID signal exists. Wrong-history, reset-hidden, and
  zero-current-response interventions change actions.
- M178: raw matched-current continuation outcome is neutral. Wrong-history does
  not create success drops on the raw surface.
- M179: boundary relocation creates local wrong-history success drops, but the
  surface is lateral-only and duplicate-dominated.
- M180: lateral and longitudinal obstacle offsets do not fix duplicate
  domination.
- M181: lowering the base action-distance threshold does not fix duplicate
  domination; the M178 candidate pool is exhausted for the current boundary
  relocation recipe.
- M182: remaking the matched-current corpus with physical-pair, left-step, and
  obstacle-bucket diversity produces a robustness-passing boundary wrong-history
  proof surface: `78` accepted success-drop rows across `15` physical pairs,
  `8` left steps, `3` targets, and `2` checkpoints.
- M183: deduplicated M182 boundary-outcome corpora pass objective sanity for
  both M168 and M170, and replay sanity reproduces normal-history success plus
  wrong-history failure on every corpus row.
- M184: a 20-step anchored actor-coupling update from M168 improves the M183
  fixed objective with tiny anchor drift, preserves behavior on seeds `9503`
  and `9504`, passes the protected key, and retains all M168/M170 boundary
  replay success drops.
- M185: a 1024-step guarded PPO smoke from M184 improves the fixed M183
  objective slightly, preserves behavior on seeds `9503` and `9504`, passes the
  protected key, and retains all M168/M170 boundary replay success drops.
- M186: independent repeats of the M185 recipe on seeds `5186` and `5187`
  preserve behavior, protected key, and M168/M170 boundary replay drops. Fixed
  objective improvement is mixed, so M185 seed `5185` remains the best retained
  fixed-loss checkpoint.
- M187: a short stage2 PPO extension from M185 seed `5185` improves fixed M183
  loss to `0.171351` and preserves behavior, protected key, and both M183
  replay surfaces.
- M188: stage2 repeats on seeds `5191` and `5192` preserve behavior, protected
  key, and both M183 replay surfaces; seed `5191` improves fixed M183 loss to
  `0.171306`.
- M189: a short stage3 continuation from M188 seed `5191` improves fixed M183
  loss to `0.171221` and preserves behavior, protected key, and both M183
  replay surfaces.
- M190: stage3 repeats preserve behavior, protected key, and both M183 replay
  surfaces, but fixed M183 loss plateaus near `0.171232`; M189 remains the
  current best fixed-loss checkpoint.
- M191: broader current-best evaluation validates M189 on fresh behavior seeds
  `9505` and `9506`, preserves the protected key, and keeps the M168/M170 M183
  replay success-drop counts at `16/16` and `17/17`. The result is positive as
  retention, but not enough to continue PPO because the proof surface is still
  inherited from M183.
- M192: a fresh current-family proof-surface refresh with seeds
  `9520`-`9523` finds `2817` matched-current pairs and passes robustness with
  `131` wrong-history success drops across `11` physical pairs, `6` left
  steps, `3` checkpoints, and `2` target groups. This refreshes evidence beyond
  M183 but still requires replay-aligned objective sanity before actor/PPO work.
- M193: converts M192 accepted rows into M184/M188/M189 boundary-outcome
  objective corpora. All three pass 3-seed objective sanity and replay gates.
  The current-best M189 corpus has `14` rows across `11` physical pairs and
  `2` targets, with `14/14` replayed success drops retained.
- M194: a single-seed tiny actor-coupling update from M189 improves the M193
  fixed objective by `0.001639` on independent eval, preserves behavior seeds
  `9505` and `9506`, passes the protected key, retains old M183 replay drops
  `16/16` and `17/17`, and retains refreshed M193 replay drops `14/14`.
- M195: fresh actor-update repeats from M189 on seeds `9851` and `9852` both
  improve the fixed M193 objective versus M189 and preserve behavior,
  protected key, old M183 replay, and refreshed M193 replay. M194 remains the
  best fixed-objective actor-update checkpoint.
- M196: a 1024-step guarded PPO smoke from M194 preserves behavior seeds
  `9505` and `9506`, passes the protected key, retains old M183 replay drops
  `16/16` and `17/17`, and retains refreshed M193 replay drops `14/14`.
  Fixed M193 loss remains better than M189 (`0.159017` vs `0.160647`) but does
  not beat M194 (`0.159008`), so the result is retention only.
- M197: fresh PPO smoke repeats from M194 on seeds `5197` and `5198` both
  improve fixed M193 loss versus M194 (`0.158919` and `0.158976` vs
  `0.159008`) and preserve behavior seeds `9505` and `9506`, protected key,
  old M183 replay drops `16/16` and `17/17`, and refreshed M193 replay drops
  `14/14`. Seed `5197` is the current best retained fixed-loss repeat.
- M198: a short stage2 from M197 seed `5197` improves fixed M193 loss to
  `0.158892`, preserves behavior seeds `9505` and `9506`, passes the protected
  key, retains old M183 replay drops `16/16` and `17/17`, and retains
  refreshed M193 replay drops `14/14`.
- M199: stage2 repeats from M197 seed `5197` on seeds `5201` and `5202` both
  improve fixed M193 loss versus M198 (`0.158850` and `0.158857` vs
  `0.158892`) and preserve behavior, protected key, old M183 replay drops
  `16/16` and `17/17`, and refreshed M193 replay drops `14/14`. Seed `5201`
  is the current best retained fixed-loss repeat.
- M200: a short stage3 from M199 seed `5201` improves fixed M193 loss to
  `0.158756`, preserves behavior seeds `9505` and `9506`, passes the protected
  key, retains old M183 replay drops `16/16` and `17/17`, and retains
  refreshed M193 replay drops `14/14`. Its smoke eval termination rate is
  elevated at `0.40`, so repeat evidence is required before further
  continuation.
- M201: stage3 repeats from M199 seed `5201` on seeds `5204` and `5205` both
  improve fixed M193 loss versus M199 (`0.158730` and `0.158755` vs
  `0.158850`), do not repeat M200's elevated smoke eval termination, and
  preserve behavior, protected key, old M183 replay drops `16/16` and `17/17`,
  and refreshed M193 replay drops `14/14`. Seed `5204` is the current best
  retained fixed-loss repeat.
- M202: a short stage4 from M201 seed `5204` improves fixed M193 loss to
  `0.158585`, keeps smoke eval termination at `0.20`, preserves behavior seeds
  `9505` and `9506`, passes the protected key, retains old M183 replay drops
  `16/16` and `17/17`, and retains refreshed M193 replay drops `14/14`.
- M203: stage4 repeats from M201 seed `5204` on seeds `5207` and `5208` both
  improve fixed M193 loss versus M201 (`0.158642` and `0.158616` vs
  `0.158730`) and preserve behavior, protected key, old M183 replay drops
  `16/16` and `17/17`, and refreshed M193 replay drops `14/14`. They do not
  beat M202 (`0.158585`), so M202 remains the best fixed-loss stage4. Seed
  `5207` has elevated smoke eval termination `0.40`, so only one short
  guarded stage5 is admitted.
- M204: a short stage5 from M202 seed `5206` improves fixed M193 loss to
  `0.158475`, keeps smoke eval termination at `0.20`, preserves behavior seeds
  `9505` and `9506`, passes the protected key, retains old M183 replay drops
  `16/16` and `17/17`, and retains refreshed M193 replay drops `14/14`.
- M205: stage5 repeats from M202 seed `5206` on seeds `5210` and `5211` both
  improve fixed M193 loss versus M202 (`0.158520` and `0.158503` vs
  `0.158585`) and preserve behavior, protected key, old M183 replay drops
  `16/16` and `17/17`, and refreshed M193 replay drops `14/14`. They do not
  beat M204 (`0.158475`), so M204 remains the best fixed-loss stage5.
- M206: a short stage6 from M204 seed `5209` improves fixed M193 loss to
  `0.158420`, has smoke eval termination `0.00`, and preserves behavior plus
  old/refreshed replay gates, but fails protected key
  `9944|perturbed|28|28` with `0/1` accepted cases. M206 is rejected; do not
  continue PPO until the protected-key failure is audited.
- M207: audits M206's protected-key failure. The selected key keeps normal
  success and large margin gap, but its normal margin moves to `0.207450`,
  above the reference `max_normal_margin = 0.2` boundary window. M204 remains
  the current best; one fresh-seed stage6 retry from M204 is pre-registered.
- M208: runs the one allowed fresh-seed stage6 retry from M204 seed `5209`.
  The retry improves fixed M193 loss to `0.158354`, keeps behavior success
  `0.8625` on seeds `9505` and `9506`, preserves old M183 replay drops
  `16/16` and `17/17`, and preserves refreshed M193 replay drops `14/14`.
  It fails the same protected key with normal margin `0.208742`, above the
  reference `max_normal_margin = 0.2`, so M208 is rejected and same-recipe
  stage6 PPO is stopped.
- M209: designs the protected-key-aware response. The repeated M206/M208
  failure is treated as single-key proof fragility: normal-history clearance
  improved out of the near-boundary window while wrong-history margin gap stayed
  large. Do not train the driver to lower clearance for the old key. Refresh a
  current-best-family multi-key protected surface before any further PPO.
- M210: fresh current-family protected-surface refresh with seeds
  `10020`-`10023` finds `1837` matched-current pairs across `209` physical
  pairs, but boundary relocation finds `0` accepted wrong-history rows. Reset
  and zero-current interventions still produce `680` and `261` accepted rows,
  so the negative result is specific to fresh wrong-history near-boundary
  evidence.

Current blocker:

```text
M192-seed control audit for current-family wrong-history boundary evidence
```

## Near-Term Rule

M206 and M208 are both rejected despite better fixed objectives because the
protected-key gate failed. The failure is now repeated, not a single-seed
accident. Do not run another same-recipe stage6 retry, do not chain from M206 or
M208, and do not loosen the protected-key threshold after seeing the result.
M210 failed to refresh a fresh current-family wrong-history protected surface.
M211 must run a seed/corpus control on the M192 probe seeds before deciding
whether the current family has truly lost fresh wrong-history near-boundary
evidence. PPO remains blocked.

## Sensor Profile Policy

Keep raw wheel, `v_parallel`, steering torque, suspension, and similar channels
as separate profile experiments only. Do not promote them into the main actor
without passing the same frozen-recipe proof gates as P0.

Suggested future profile ladder:

| Profile | Inputs |
| --- | --- |
| P0 | current no-wheel human-view baseline |
| P1 | commands + actuator feedback + `ax/ay/yaw_rate` + scene |
| P2 | P1 + steering torque / EPS current |
| P3 | P2 + raw four-wheel `R omega` |
| P4 | P3 + roll/pitch/vertical acceleration |
| P5 | P4 + suspension / wheel travel |

Every profile must use the same gate sequence: probe, frozen PPO recipe,
matched-current wrong-history, reset/zero-current ablation, and outcome boundary
proof. Do not tune PPO separately for one profile and compare it directly.
