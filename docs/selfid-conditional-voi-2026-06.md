# Conditional VoI: Precise mu Given A Coarse Side-Channel Prior (2026-06)

## Status

- scope: feasibility-audit task-DESIGN measurement only. Tests the user
  proposition "side channels (road appearance / wipers / temperature) only
  bound mu to a coarse range (literature precision ~ +/-0.2..0.3); precise
  capability knowledge requires command->response self-identification".
  Formalized as: is conditional VoI = VoI(precise mu | coarse bin known)
  significantly positive? No driver-performance, repair, validation, ranking,
  promotion, paper, or self-ID *capability* claim is made.
- script: `scripts/feasibility_audit/voi_conditional_prior.py`
  (`PYTHONPATH=src python scripts/feasibility_audit/voi_conditional_prior.py`,
  deterministic, pure CPU, 340 s measured)
- results: `experiments/feasibility_audit/voi_conditional_prior.json`
- per-episode rows: `runs/feasibility_audit/voi_conditional_prior/episode_rows.csv`
  (10010 rows)
- builds on: Task B `docs/selfid-commitment-task-voi-design-2026-06.md`
  (B2 family), Task C `experiments/feasibility_audit/voi_commitment_adversarial_audit.json`
  (discrete-B2 augmented VoI anchor 0.4375).

## Setup (measured machinery)

Continuous-mu B2 variant: mu on a 12-point deterministic midpoint grid per
prior bin (~U(bin)); hazard distance follows the monotone B2 mu<->d mapping by
piecewise-linear interpolation through (0.30,24), (0.55,38), (0.85,49),
(1.15,62) m (linear extrapolation outside); every mu point is an exact
`build_env_config` member (degenerate `mu_range`/`distance_range`). All other
B2 knobs unchanged (reveal 12 m, max_steps 285 = 5.7 s, obstacle half-width
1.25 m, v0 = 8 m/s).

Conditional VoI(bin) = E_mu[per-mu oracle] - max_{bin-aware fixed plan}
E_mu[outcome]. Bin-aware fixed plans (the "coarse prior is enough" adversary):

- entry-speed commitment grid 4.5..14.0 m/s (0.5 step) x 2 steering variants,
- 9 reveal-silence ladders (continuous Task-C ladders: allowed to use the BIN
  and own driven distance, freeze at reveal),
- robust-CEM plan (4 params, 3 iters x pop 12, optimizes the bin average).

Per-mu oracle: best of all candidates at that point + local +/-0.25 m/s
refinement + reduced-budget per-mu CEM when below 1.0. Split-seed protocol:
selection on 2 seeds, headline numbers re-evaluated on 2 disjoint validation
seeds (per-point seed formula `20260611*10 + {0,1|100,101} + 17*point + 1000*k`).

Prior bins (side-channel precision tiers): full [0.25,1.15] (no-prior
control), wide +/-0.30 [0.40,1.00], medium +/-0.20 [0.45,0.85], narrow
+/-0.10 [0.55,0.75].

## Headline (measured): conditional VoI vs prior width

Base family (B2 knobs unchanged), success criterion
`outcome_bucket == success_obstacle_pass`:

| prior bin | half-width | VoI(success) in-sample | VoI(success) validated | oracle val | best fixed val (plan) | VoI(return) val |
|---|---|---|---|---|---|---|
| narrow [0.55,0.75] | 0.10 | 0.000 | -0.083 | 0.917 | 1.000 (ladder_d1_m3) | +0.9 |
| medium [0.45,0.85] | 0.20 | 0.000 | 0.000 | 1.000 | **1.000 (grid_v9.5_A)** | -0.8 |
| wide [0.40,1.00] | 0.30 | 0.167 | 0.000 | 0.917 | 0.917 (cem_robust v=9.75) | -1.6 |
| full [0.25,1.15] | 0.45 | 0.333 | **0.208** | 0.917 | 0.708 (grid_v11.5_A) | +4.1 |

Hard upper bounds independent of oracle quality (success <= 1 and the
measured best fixed plan is an achievability lower bound): conditional
VoI <= 1 - best_fixed_validated = **0.0 (narrow), 0.0 (medium), 0.083 (wide)**,
0.292 (full).

- At +/-0.20 prior, a single fixed 9.5 m/s commitment passes ALL 12 mu points
  on both selection and validation seeds -- precise mu adds nothing.
- At +/-0.30, the robust-CEM plan (v=9.75, cap 0.98, offset 2.9, gain 2.9)
  reaches 11/12 validated; conditional VoI <= 0.083.
- The no-prior control reproduces a positive VoI (0.208 validated / 0.333
  in-sample) -- but far below the discrete-B2 anchor 0.4375
  (`experiments/feasibility_audit/voi_commitment_adversarial_audit.json`):
  continuizing mu and densifying the hedge grid already destroys roughly half
  of the discrete family's VoI. The 4-theta design (gaps of 0.30 in mu)
  behaves like a wide-prior world, not a no-knowledge world.
- VoI(return) is <= 4.1 validated on a ~265 return scale (<2%) everywhere:
  the return channel never carried the proposition.

## Mechanism (measured): feasible entry-speed bands

Per mu point, the fully-passing entry-speed band [v_min, v_max] (grid variant
A, both selection seeds; see `mechanism.bands_per_mu_point` in the JSON):

- band TOP (collision/dodge limit) moves at 6.4-8.2 m/s per unit mu; band
  BOTTOM (deadline limit) at 5.5-8.5 m/s per unit mu; typical band width
  1.5-3.5 m/s.
- Coverage arithmetic (inferred from the measured bands): a prior of mu-width
  w is hedgeable by one speed iff shift * w <= band width. Measured band
  intersections over the bin: narrow [8.5,9.5] (width 1.0), medium exactly
  {9.5} (width 0.0), wide empty (-1.0), full empty (-3.5).
- Where the intersection is empty (wide/full) the silence ladders and
  robust-CEM partially substitute for mu knowledge: silence past driven
  distance p implies mu > mu_of_d(p + 12), because hazard distance is
  perfectly mu-correlated -- ladder_d1_m3 scores 0.583 (wide) / 0.833 (medium)
  and cem_robust 0.833 (wide) selection-seed mean without any
  self-identification.
- Knife-edge caveat (measured): the empirical per-point oracle prefers the
  fastest succeeding plan (return grows with speed), which sits at the band
  top; 1 of 12 points per bin flipped on validation seeds (e.g. mu=0.662/0.675
  grid_v12 cells 1.0 -> 0.0), which is why validated oracle reads 0.917 in
  three bins. In-sample numbers are the optimistic bound, validated the
  conservative one.

## Knob iteration (measured): can the task be made prior-robust?

Trigger: medium-bin VoI 0.000 < target 0.20. Iterated on wide+medium bins
only (`knob_iterations` in the JSON):

| variant | knobs | medium VoI in/val | wide VoI in/val | target met |
|---|---|---|---|---|
| K1_deadline265 | deadline 5.7 -> 5.3 s | 0.125 / 0.000 | 0.333 / 0.250 | no |
| **K2_reveal10** | reveal 12 -> 10 m | **0.375 / 0.292** | 0.500 / 0.375 | **yes** |
| K3, K4 | not run (K2 met target first) | - | - | - |

K2 mechanism (measured): with a 10 m reveal the dodge limit drops sharply and
the bands collapse to width 0-1.5 m/s (e.g. mu=0.575 band [7.5,7.5], mu=0.825
[9.5,9.5]); no single speed covers even +/-0.20 (best fixed grid_v9_A 0.667
validated), and the silence ladders collapse too (best bin-aware
ladder/cem 0.417 selection mean vs 0.833-0.875 at reveal 12): less reveal
distance simultaneously means less escape capacity AND less pre-reveal
silence information. Caveat: K2 validated oracle is 0.958 (medium) / 0.917
(wide) -- the tighter family is more knife-edge, so a higher-seed oracle pass
is required before using K2 in any gate.

## Verdict

**Partially refuted on the unmodified family; restorable by one knob.**

1. On the UNMODIFIED continuous B2 family the user proposition is REFUTED at
   realistic side-channel precision: given a +/-0.20 or +/-0.30 mu bin, a
   bin-aware fixed plan recovers the oracle to within 0.000/0.083 success
   (hard bounds) -- coarse appearance/wiper/temperature priors plus hedging
   are sufficient; instruction-response identification adds ~nothing.
2. The proposition survives only without any prior (full-domain VoI 0.208
   validated), and the discrete 4-theta B2 measurement (VoI 0.4375-0.5625)
   overstates the continuous value of self-identification by ~2x.
3. The task is NOT expressiveness-limited: tightening
   `perception_reveal_distance` 12 -> 10 m makes conditional VoI 0.292 at
   +/-0.20 (>= 0.20 target), i.e. a B2-K2 family where the proposition HOLDS
   exists inside the current env.

## Implications for experiment design (inferred)

1. Any self-ID gate built on B2 must include a "free coarse prior" control
   arm: hand the policy the +/-0.2 bin (e.g. as an observation constant)
   without precise mu. On unmodified B2 this control should saturate at the
   fixed-plan ceiling (1.000 at medium) -- if a "self-identifying" policy only
   matches it, the policy may have learned a bin hedge, not identification.
2. If the realistic assumption is "side channels exist", gates should use the
   K2 (reveal 10 m) variant, with the gate-3 bar recomputed as
   best_fixed_val + 0.5 * VoI_val = 0.667 + 0.146 = 0.813 at +/-0.20.
3. Knife-edge density rises as knobs tighten; gate measurements on K2 need
   more validation seeds (the 2+2 protocol here flips ~1/12 points).

## Reproduction

```
PYTHONPATH=src python scripts/feasibility_audit/voi_conditional_prior.py            # full (~340 s)
PYTHONPATH=src python scripts/feasibility_audit/voi_conditional_prior.py --quick    # smoke (~90 s)
```
