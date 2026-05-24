# Current Status

This file is the compact official state for the project. Milestone documents
remain the detailed experiment log.

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

Latest public-gate base:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

Status: M400 promoted M399 alpha `0.05` as the current public-gate base after
six public replay surfaces and behavior seeds passed. M487-M529 did not promote
a new driver checkpoint.

Latest infrastructure smoke checkpoint:

```text
runs/m528_l0_current_observation_smoke/checkpoint.pt
```

Status: M528 smoke-only L0 current-observation checkpoint. It validates
baseline route and metadata, not driver performance.

## Current Blocker

```text
m531-matched-history-short-train-config-design
```

M531 should pre-register the matched L0/L2/L3 short-train config family with
shared budgets, seeds, configs, evaluation surfaces, and artifact retention
rules before running any trained-baseline comparison. It must not promote a
checkpoint or tune one baseline independently.

## Recent Evidence Line

- M520 valid-offset projected replay produced only a margin-only projected
  history signal: `1` source-narrow wrong-history proof candidate and `0` event
  rows.
- M524 found stronger natural history-value diagnostics: `480` L0 diagnostic
  candidates and `18` obstacle-completion event rows across natural M497/M487
  surfaces.
- M526 audited those event rows as source-diverse diagnostic evidence:
  `18` obstacle-completion drops across `2` surfaces, `5` probe seeds, and
  `2` targets, with projected event rows excluded.
- M527 defined the matched baseline family: L0 feedforward/current observation,
  L1 one-step command-response annotation, L2 finite command-response window,
  and L3 online GRU recurrent belief.
- M528 implemented explicit baseline metadata and an L0 smoke path while
  preserving the P0 no-wheel/no-oracle actor contract.
- M529 pre-registered the staged matched-baseline evaluation ladder so later
  L0/L2/L3 comparisons use shared budgets, seeds, configs, artifacts, and
  holdout discipline.
- M530 repeated the L0 current-observation smoke on seeds `3530` and `3531`.
  Both completed and wrote stable `L0_current_observation` plus
  `P0_human_view_no_wheel_no_oracle` metadata. The smoke returns are not
  interpreted as baseline evidence.

## Near-Term Rule

Do not treat reset-hidden diagnostics or M528 smoke return as trained baseline
evidence. The next branch must first establish repeatable baseline plumbing,
then move to matched short-train comparisons with shared recipes. Any later
promotion requires proof retention, generalization retention, behavior
retention, no contract violation, and clear lineage.

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
