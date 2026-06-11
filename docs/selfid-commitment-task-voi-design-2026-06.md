# Self-ID Commitment Task: VoI-Positive Scenario Family Design (2026-06)

## Status

- scope: task-family DESIGN measurement only (Task B of the feasibility-audit
  self-ID takeover route). No driver-performance, repair-success,
  robustness-result, validation, ranking, winner-selection, checkpoint, paper,
  or self-ID *capability* claim is made.
- script: `scripts/feasibility_audit/voi_commitment_task_design.py`
  (`PYTHONPATH=src python scripts/feasibility_audit/voi_commitment_task_design.py`,
  deterministic, pure CPU, ~76 s)
- results: `experiments/feasibility_audit/voi_commitment_task_design.json`
- per-episode rows: `runs/feasibility_audit/voi_commitment_task_design/episode_rows.csv` (2080 rows)

## Headline (measured)

| metric | value | target | met |
|---|---|---|---|
| VoI(success), in-sample | **0.516** | >= 0.25 | yes |
| VoI(success), split-seed validated | **0.5625** | >= 0.25 | yes |
| per-theta oracle success | 1.000 (in-sample & validated) | - | - |
| best fixed-plan success | 0.484 (in-sample) / 0.4375 (validated) | - | - |
| VoI(return), in-sample | 12.2 | - | secondary |
| linear probe R^2 (probing actions -> mu) | **0.9999** (raw history) | >= 0.30 | yes |
| linear probe R^2 (no probing, steady tracking) | 0.0098 | contrast | - |

Context: Task A measured the CURRENT task family at `voi_success == 0` on all
24 skeletons (`experiments/feasibility_audit/voi_current_task_family.json`,
`overall.voi_success.max = 0.0`). This document shows the zero is a property
of the task design, and exhibits a family where it is structurally positive.

## Why the current family has VoI(success) = 0 (dominance argument, inferred)

For any scenario family in this env where

1. success is monotone in mu for every fixed plan (more grip never hurts),
2. any mu_low-safe speed profile is mu-agnostically executable (speed is an
   observable channel, so "track this v(t)" needs no mu knowledge), and
3. the success criterion has no mu-dependent threshold,

the per-plan success region in mu is upward-closed, the feasible-theta set is
the union of upward-closed sets, and the most cautious feasible plan attains
it everywhere. Hence `max_fixed E_theta[success] = E_theta[oracle success]`,
i.e. VoI(success) = 0 identically -- knowing mu can help the *return* (Task A:
VoI_return mean 3.53) but never flips a success outcome. All ~1500 self-ID
milestones trained inside families of this type.

## Design principle: anticipatory entry-speed commitment

Source thesis: a human driver on an unknown-grip road chooses the corner-entry
speed BEFORE seeing the hazard (anticipatory), not after (reactive). The
design breaks assumption (3) above with a deadline x late-reveal x
mu-correlated hazard structure:

- **preparation segment**: quasi-straight approach (circle track r=900 m,
  effectively straight over <70 m), every episode starts at v0 = 8 m/s with
  `friction_limited_speed=false`, so the start leaks NO mu information; mu is
  inferable only from one's own command->response history (probe pulses).
- **late reveal**: `obstacle.perception_reveal_distance = 12 m` -- the hazard
  becomes visible too late to shed speed on low grip (reveal timing set by the
  unavoidability physics below and confirmed by measurement).
- **hard deadline**: `max_steps = 285` (5.7 s) + `finish_on_pass=true`;
  success = `outcome_bucket == success_obstacle_pass`. Arriving slow is safe
  but, on far-hazard episodes, cannot finish in time -- this is the reward/
  feasibility tension that makes mu worth knowing BEFORE the reveal.
- **mu-correlated hazard distance**: low grip => near hazard (slow entry both
  sufficient and deadline-feasible); high grip => far hazard (only a fast,
  committed entry meets the deadline; fast entry on low grip is physically
  unrecoverable at reveal).

### Reveal-timing unavoidability calculation (inferred, design aid)

Point-mass bound at the reveal (lateral capacity `0.5 * 0.85 * mu * g * t^2`
with `t = D_reveal / v_arrival`, required offset = 0.90 + 1.25 + 0.30 =
2.45 m): at mu=0.30 a fast plan arrives at ~9.9 m/s (traction-limited
acceleration from 8 m/s) with t ~ 1.06 s and capacity ~1.6 m < 2.45 m =>
unavoidable; a 5 m/s arrival has t ~ 2.3 s and capacity ~6.8 m => avoidable.
The earlier candidate with reveal at 14 m measurably let fast plans survive
mu=0.30 (matrix top row all-success), so the reveal was tightened to 11-12 m;
at 12 m the fast-on-low cells measure 0.00-0.06 success.

## Final scenario family (B2_mu_correlated_hazard_tight)

Shared knobs (each theta member is fully expressible through
`autodrift.config.build_env_config`): circle track r=900 m, track_width 5.0,
dt 0.02, v0 = 8 m/s (`speed_range=[8,8]`, `friction_limited_speed=false`),
obstacle half-width 1.25 m (required lateral offset 2.45 m), reveal distance
12 m, `max_steps=285` (deadline 5.7 s), `finish_on_pass=true`
(`finish_pass_distance=2`), `pass_reward=10`, `collision_penalty=20`, all
non-mu randomization pinned to 1.0, obstacle lateral offset compensates the
arc-vs-tangent placement (`R - sqrt(R^2-d^2)`).

| theta | mu | hazard distance d (m) | oracle entry speed (m/s) | oracle plan (measured) |
|---|---|---|---|---|
| 1 | 0.30 | 24 | 5.0 | swerve_only_v5 |
| 2 | 0.55 | 38 | 7.5 | swerve_only_v7.5 |
| 3 | 0.85 | 49 | 10.0 | commit_v10 |
| 4 | 1.15 | 62 | 13.0 | swerve_only_v13 |

## Measured success matrix (16 seeds/level, 13 mu-agnostic plans)

| plan | mu 0.30 | mu 0.55 | mu 0.85 | mu 1.15 | mean |
|---|---|---|---|---|---|
| swerve_only_v5 | **1.000** | 0 | 0 | 0 | 0.250 |
| swerve_only_v7.5 | 0.875 | **1.000** | 0 | 0 | 0.469 |
| swerve_only_v10 (best fixed) | 0.062 | 0.875 | **1.000** | 0 | **0.484** |
| swerve_only_v13 | 0 | 0 | 0.500 | **1.000** | 0.375 |
| commit_v5 / v7.5 / v10 / v13 | 0.688/0/0.062/0 | 0/0.750/0/0 | 0/0/1.000/0 | 0/0/0/0 | <=0.266 |
| always_crawl_v4.5 | 0.688 | 0 | 0 | 0 | 0.172 |
| always_max_v14.5 | 0 | 0 | 0 | 0 | 0.000 |
| ladder_adaptive (mu-agnostic elimination) | 1.000 | 0 | 0 | 0 | 0.250 |
| aeb_reflex_v8 (reactive only) | 0 | 0 | 0 | 0 | 0.000 |
| probe_then_commit_v7.5 | 0 | 0.688 | 0 | 0 | 0.172 |

- VoI(success) = E_theta[max_plan] - max_plan E_theta = 1.000 - 0.484 =
  **0.516** (in-sample); split-seed validated (plan selection on even seeds,
  evaluation on odd seeds): 1.000 - 0.4375 = **0.5625**.
- The natural mu-agnostic counter-strategies are in the family and lose to the
  deadline: the position-indexed "ladder" (drive slow until each hazard
  position is ruled out, then speed up) succeeds only on theta1 (0.25); the
  pure reactive AEB reflex scores 0.
- Reward tension (measured returns): `always_crawl_v4.5` earns 121-149 across
  levels, while the theta4 oracle `swerve_only_v13` earns 377 on mu=1.15 --
  "always slow" is strictly dominated when mu is known to be high; VoI(return)
  = 12.2 in-sample.

## Candidate iteration (measured, 6 seeds/level)

| candidate | geometry | VoI in-sample | VoI split-validated | oracle | best fixed |
|---|---|---|---|---|---|
| A1_independent_geometry | d ~ U(24,60) independent of mu, deadline 5.8 s | 0.208 | 0.083 | 0.667 | 0.458 |
| A2_independent_mild_deadline | d ~ U(24,48), deadline 6.4 s | 0.167 | 0.083 | 0.875 | 0.708 |
| B1_mu_correlated_hazard | d in {24,38,48,60} by mu, reveal 11 m | 0.583 | 0.417 | 1.000 | 0.417 |
| **B2_mu_correlated_hazard_tight (selected)** | d in {24,38,49,62} by mu, reveal 12 m, w=1.25 | 0.542 | 0.500 | 1.000 | 0.458 |

A-variants (expressible in a SINGLE env config) stay under the 0.25 bar: with
d independent of mu the slow oracle leaks deadline failures on far hazards
(multiplicative structure, analytic sup ~0.28 -- inferred), and measured VoI is
0.17-0.21. Crossing the bar robustly required the mu-correlated mixture.

## Inferability lower bound (measured)

Continuous mu ~ U(0.25, 1.15), 200 episodes/condition, 110-step preparation
window (no reveal inside the window), features = observation channels 0-11
(ego response + previous command, same channels as the
selfid_task_health_check Phase-D probe), episode-level 60/20/20 ridge with
alpha picked on validation, test R^2:

| condition | R^2 raw history | R^2 summary features |
|---|---|---|
| probe pulses (brake/throttle/steer pulses during tracking) | **0.9999** | 0.9999 |
| no probe (steady speed tracking) | 0.010 | -0.010 |
| bounded random actions | -0.383 | 0.742 |

Physics: at v0=8 m/s a full-brake pulse is traction-limited for mu < ~0.89 and
a 0.5-amplitude steer pulse saturates the front axle for all mu <= 1.15, so
the response history is informative across the whole range -- but ONLY under
deliberate excitation; steady tracking reveals nothing (R^2 ~ 0.01). The task
therefore rewards *active* self-identification during the preparation segment.

## Observable signatures of a theta-aware policy (for a future gate)

Measured oracle behavior on the final family: oracle entry speed is perfectly
rank-correlated with mu (Spearman = 1.0 over the 4 levels: 5.0/7.5/10/13 m/s
at mu 0.30/0.55/0.85/1.15). Proposed gate signatures:

1. reveal-crossing speed rank-correlated with episode mu (Spearman >= 0.8)
   while mu is hidden until the reveal -- only achievable through pre-reveal
   inference;
2. preparation-segment action energy above the no-probe baseline
   (`prep_action_sq_mean` in the episode rows) -- evidence of active probing;
3. panel success >= best_fixed_validated + 0.5 * VoI_validated
   (>= 0.4375 + 0.281 = 0.72 on this family) -- the policy must realize a
   meaningful share of the measured VoI, which no fixed plan can.

## Env expressiveness gaps (what a native implementation needs)

1. **mu-correlated hazard distance**: currently a MIXTURE of per-theta env
   configs; one config cannot couple `randomization.mu_range` with
   `obstacle.distance_range`. Needed knob: conditional obstacle distance
   sampling given the drawn mu (e.g. `obstacle.distance_from_mu` table).
2. **initial speed**: always `speed_ref`; an independent `initial_speed_range`
   would make the entry-speed commitment cleaner (worked around by giving the
   preparation segment enough length to reach any commitment speed from 8 m/s).
3. **reward target**: `speed_ref` doubles as the reward speed target
   (`speed_cost`), so slow commitments pay a flat reward penalty on all theta;
   acceptable here because success-VoI is deadline-driven.

`perception_reveal_distance`, `finish_on_pass` + `max_steps`, degenerate
randomization ranges, and the obstacle lateral-offset knob were sufficient for
everything else.

## Reproduction

```
PYTHONPATH=src python scripts/feasibility_audit/voi_commitment_task_design.py            # full (~76 s)
PYTHONPATH=src python scripts/feasibility_audit/voi_commitment_task_design.py --stage smoke
PYTHONPATH=src python scripts/feasibility_audit/voi_commitment_task_design.py --quick
```

Seeds: panel `20260612*10 + level_index*1000 + k`; probe
`20260612*100 + mode*10000 + episode`. All rollouts use
`autodrift.evaluate.outcome_bucket_from_info` semantics.
