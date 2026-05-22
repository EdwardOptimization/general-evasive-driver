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

Current blocker:

```text
turn the M182 source-diverse proof surface into a replay-aligned objective
```

## Near-Term Rule

Do not run PPO directly from the M182 rows. First build a deduplicated
boundary-outcome corpus/objective and prove objective improvement is aligned
with replayed boundary outcomes.

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
