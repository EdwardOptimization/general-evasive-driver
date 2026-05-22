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

Current blocker:

```text
tiny guarded PPO smoke from M194 before any longer PPO continuation
```

## Near-Term Rule

Only a tiny guarded PPO smoke is admitted, starting from M194. Do not run a
longer PPO continuation until the smoke preserves behavior, protected key, old
M183 replay, and refreshed M193 replay.

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
