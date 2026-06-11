# AutoDrift Phase-2 Research Plan: Capability-Boundary Tracking (v2, 2026-06-11)

## 0. Status and scope

- kind: research plan (manual takeover session); supersedes the paused
  paper-route and self-ID branch plans as the active program definition.
  Takeover rationale: `docs/feasibility-takeover-2026-06-route-decision.md`.
- governing thesis: `docs/capability-boundary-tracking-thesis-2026-06.md`
  (four-loop driver mechanism; two-regime law, Section 8).
- revision: v2 after three-way adversarial review (science/statistics,
  engineering grounding, deployability narrative); v1 deltas are tracked in
  the commit message.
- process registration: WP0-WP4 measurement/implementation units are
  registered as harness milestones (M3215+) with manifests and
  pre-registration artifacts for provenance. WP6.2 guardrails are now live;
  autonomous/Codex sessions execute only through the ordered Phase-3 roadmap
  and PI checkpoints.
- live progress and gate dispositions after this plan are tracked in
  `docs/current-status.md`; this plan remains the program/criteria
  definition and may retain work-package wording that was later completed
  or closed by gates.
- claim boundary: this document plans work; it asserts no result beyond the
  cited artifacts.

## 1. Position (what is already established, with artifacts)

1. **Reflex layer hard-safety ceiling certified.** v4 incumbent: 100% on
   feasible rows of the original fixed panel (55/55); on the extended
   feasible panels 5 known zero-collision offtrack failures remain (v5
   fixes 2, 3 outstanding); **0 collisions on all 172 feasible fresh-seed
   episodes**. Residual 7 rows oracle-certified unavoidable (43,372
   privileged rollouts). v5 is net-negative in deep overshoot (paired
   v4-only saves 26/28 vs v5-only 0). HF4: 249/256 outcomes identical under
   Chrono::Vehicle; zero new hard-safety failures.
2. **Two-regime law (single task family).** Clean sensing: VoI(belief)=0 at
   every reveal window 9.5-30 m — a belief-free threshold-seeker (embedded
   shortfall identification, 140-400 ms; reflex rescue budget 92.6% save)
   matches the per-mu oracle. Degraded sensing: VoI(belief) revives to
   **0.17-0.88 in 12/14 cells vs the seeker floor** (all 7 tightest-window
   cells >= 0.21; 100 ms self-response delay alone reopens +0.208).
   Honest restatement against the **best belief-free arm** (max over seeker
   variants and fixed plans): range ~0.17-0.67 and **11/14 cells** (the
   12 m/500 ms/clean cell drops to 0.083). Anchor caveat: the clean-oracle
   anchor grants the belief side dead-reckoning, legitimate in-sim only
   because dynamics are deterministic and the command channels are not
   degraded; the matched (same-cell degraded) oracle anchor is the
   deployable-primary reference (Section WP1).
3. **Why ~1500 self-ID milestones nulled**: the old task family had
   VoI(success)=0 (24/24 skeletons); probe-based designs leak through
   persistent state; the value lives in detection speed and rescue
   bandwidth under clean sensing, re-emerging as *precise* belief only
   under degraded sensing in tight windows (coarse +/-0.2 priors do not
   substitute).
4. **Infrastructure**: deterministic env reconstruction to 1e-6;
   observation-degradation wrapper integrated across train/eval/gate
   (M3214; constant integer delay + iid Gaussian only — extensions are WP0
   engineering); oracle/CEM and regime measurement machinery;
   SlipOnsetDetector (obs72-only); staged-training discipline (m1087);
   throughput: 16 concurrent single-thread jobs aggregate ~12.9k env
   steps/s (single training job ~0.8-1.3k steps/s); CUDA measured 2.6x
   slower for this model class.

### Shorthand index

| code | meaning | artifact |
|---|---|---|
| obs72 / action3 | 72-dim actor observation contract / [steer, throttle, brake] | `docs/observation-contract.md` |
| B2K2_final | commitment task family (continuous mu, reveal 9.5 m, jitter, rewards 40/60) | `experiments/feasibility_audit/selfid_task_final_spec.json` |
| K2 | reveal-distance tightening that makes precision pay (12->10->9.5 m) | `docs/selfid-conditional-voi-2026-06.md` |
| measurement A/B/C | onset detectability / ramp-policy regime map / reflex recovery budget | `docs/selfid-threshold-seeking-{onset,regime}-2026-06.md`, `docs/selfid-reflex-recovery-budget-2026-06.md` |
| G1' | supervised ignition gate (failed: BC compounding + speed-register leak) | `docs/selfid-g1prime-ignition-gate-2026-06.md` |
| P1 residual | reward-success Spearman 0.81-0.88 < 0.9 on the final spec | `docs/selfid-task-final-spec-2026-06.md` |
| m1087 | staged-training discipline (BC -> capability pretrain -> guarded RL) | `docs/m1087-staged-training-discipline-harness-rule.md` |
| M1182 | the original FIR-vs-GRU (finite window vs recurrent) question | `docs/paper-route-finite-window-vs-gru-plan.md` |
| HF4 | dual-backend same-scenario discrepancy measurement | `docs/feasibility-route-hf4-full-discrepancy-2026-06.md` |
| gate protocol v2 | anchors before informative actions; R^2<=0.1 self-check | `docs/selfid-gate-protocol-v2-2026-06.md` |

## 2. Central claims to establish or refute

- **C1 (generality)**: the two-regime law holds beyond the B2K2 family —
  on a second task geometry and under richer degradation models.
- **C2 (learnability of belief)**: a learned history-borne capability
  estimator recaptures a pre-registered fraction of the **matched-anchor**
  degraded-regime prize when substituted for true mu in the same planner.
- **C3 (FIR vs IIR)**: long finite windows (L2) vs recurrent state (L3)
  discriminated on a variant where the excitation-to-decision gap provably
  exceeds the FIR window — resolving M1182 on the first testbed with a
  measured positive prize.
- **C4 (deployable architecture)**: belief -> envelope constraint ->
  short-horizon sequence proposal -> verifier (recoverable-set check) ->
  execute u0 -> reflex fallback, with the verifier operating only on
  *believed* parameters, beats the belief-free stack exactly where the
  regime map says it should. [Status: closed by G-B/G-C — WP2 did not
  open; scope contracted per the gates.]
- **C5 (one policy for all passenger cars; PI directive 2026-06-11,
  scope corrected same day)**: the target population is **the entire
  passenger-car fleet** — one controller serving sedans, SUVs, sports
  cars, vans (~900 kg to 3+ t, wide geometry/authority/actuation
  ranges) — not within-model variation. Under that population spread
  combined with handling-limit demand, an RL policy trained across the
  population outperforms BOTH the fixed-parameter reflex AND the
  classical identification-plus-retuning scheme. PI's argument: even one
  model varies hugely (load, season, modification), so across the whole
  fleet per-vehicle hand-tuning is out of the question; RL internalizes
  vehicle-and-limit identification in the network (massively evidenced
  in robotics: RMA/UP-OSI) and commands actuators directly, enabling
  nonlinear-regime actions. Grounding in our measurements: the Section-10
  capstone makes implicit adaptation the *natural* form of competent
  closed-loop behavior (RL's home turf, attribution not required); the
  reflex family is proven incapable of beyond-saturation operation
  (0/84) while RL reached 0.906 on an all-AEB-infeasible surface;
  vehicle uncertainty alone lifts the detection floor 0.08 -> 0.29.
  **Judging discipline: engineering-only** — closed-loop outcomes vs
  floors and per-instance oracles; no history-attribution claims (the
  capstone explains why none are possible or needed).

## 3. Deployability claim boundary (PI requirement)

1. **In-narrative (sell)**: production sensing stacks (filtered IMU,
   estimator + bus chains >= 100 ms) live in the degraded regime by
   default — the two-regime law's deployment reading is that *the belief
   layer is not optional in production conditions*; the clean regime is an
   idealization only simulators reach.
2. **In-narrative (certification path)**: the certifiable objects are the
   verifier + reflex layer ("never command a state the reflex cannot
   recover"); the belief estimator needs performance-grade, not
   safety-grade, assurance because the verifier bounds the harm of wrong
   beliefs — backed by the WP2 adversarial wrong-belief stress test.
3. **Out of scope (declared)**: recoverable-set calibration on real
   dynamics (measurement C is in-sim synthetic-state injection; real-car
   calibration is Phase-3+; we ship sim-certified + Chrono directional
   checks only).
4. **Out of scope (declared)**: active limit-probing as a product behavior
   (threshold-seeking remains a scientific control, not a product claim;
   comfort/regulatory constraints on excitation are acknowledged, not
   engineered here).

## 4. Work packages

### WP0 — Coverage completion (prerequisite for C1)

Engineering precondition (~1 day, before any CPU hours): extend the M3214
wrapper with AR(1) correlated noise, frame dropout, and time-varying delay
modes (new unit tests; clean-anchor bit-reproduction preserved;
`[stream, seed_root, episode]` derivation backward-compatible). Optional
S1 axis: actuation delay + slew-rate limit wrapper branch (production
brake-hydraulics realism; note it weakens the dead-reckoning legitimacy of
the clean anchor — re-examine WP1 anchors if enabled).

1. **Family #2 (pinned)**: primary = large-radius straight + laterally
   offset single obstacle (asymmetric gap choice; expressible today via
   `lateral_offset_range`); fallback = S-curve entry only if figure_eight
   integration is separately funded. Construction discipline: <= 3
   candidate geometries, all reported; construction criterion (commitment
   VoI >= 0.25) is distinct from the tested readouts (clean VoI(belief)
   and degraded revival), breaking the circularity objection. Reuses the
   per-cell degenerate-config mechanism from `ramp_policy_voi_regime.py`.
2. **Degradation realism with a falsifiable bridge**: for each new model
   (AR(1) rho x sigma, dropout p, time-varying delay), first measure the
   calibrated detector's median detection-latency increase dL on sub-limit
   ramps (measurement-A protocol, no task outcomes consulted); prediction:
   the cell's VoI equals the pure-delay cell at delay = dL (interpolated).
   Pass = threshold classification (VoI >= 0.15 or not) agrees on >= 75%
   of new cells AND Spearman(predicted, measured) >= 0.6, on validation
   seeds. AR(1) genuinely threatens the prediction (it defeats
   time-averaging) — that is the point.
3. **Statistical hardening**: every cell entering a paper main table gets
   >= 10 validation seeds (>= 120 episodes) with Wilson CIs; regime-edge
   cells get a continuous reveal-window sweep. Clean-sensing replication
   criterion: seeker-vs-oracle gap <= 0.05 on >= 120 validation episodes.
   (Full degraded matrix at 5x seeds ~ <1.5 h CPU.)
4. **Moving obstacles: explicitly out of week-1 scope.** A constant-velocity
   crosser is a separate env engineering task (obstacle kinematics,
   collision geometry, feasibility-label re-derivation; >= 1-2 days);
   legacy zero-rel-vel validators untouched. Scheduled only after G-B.
5. Beyond-saturation drift-equilibrium stabilizability (thesis Section 5.1
   queue): **de-scoped to Phase-3** — the 3 drift_required rows are
   oracle-certified unreachable for this controller family and block none
   of C1-C4.

Acceptance: regime-law direction replicated on family #2 (clean
VoI(belief) <= 0.05; degraded >= 0.15 in tight windows, both on hardened
validation sets); degradation-model placements pass the bridge criterion.
Budget: ~1-2 engineering days + ~4 h CPU. Stop rule: refutation on family
#2 demotes the law to family-specific and re-scopes papers — itself a
publishable outcome.

### WP1 — Modular belief experiment (C2 + C3; the learning gate)

Decouples "can belief be learned" from "can control be learned". New code
(~0.5-1 day): supervised estimator training script + a belief-injection
hook in the seeker (replacing its internal `_mu_eff`); reuses the G1'
protocol skeleton (seed discipline, paired eval, leak checks).

1. **Data**: on-demand rollouts on the degraded tight-window family.
   **Behavior policy decoupled from mu** (anti-leak, the G1' speed-register
   lesson applied to training distributions): fixed plans + ramp families
   with randomized target speeds; before any training, report the
   decision-frame single-frame->mu probe R^2 on the collected dataset —
   **<= 0.1 gates data acceptance** (linear probe primary, small-MLP probe
   secondary). Labels: primary = mu_eff (the planner interface consumes
   mu); feasible-speed band = secondary, exploratory. Training rollout
   seed stream = a new SEED_BASE, disjoint from the regime measurement's
   selection and validation streams.
   **Heterogeneous-belief fixtures** (from
   `docs/selfid-belief-decomposition-2026-06.md`): if vehicle
   randomization is on, episodes carry a **5 s sub-limit familiarization
   prefix as a standard fixture**, and the belief-free floor includes
   prefix + vehicle-RLS — otherwise the prize over-counts the vehicle
   share (+0.15-0.19) that 5 s of ordinary driving recovers for free. The
   estimator design is asymmetric two-timescale: slow vehicle channel
   (RLS on the authority ratios; <= 5 s convergence; under noise requires
   an errors-in-variables/IV fix using the undegraded command channels
   9-11 — naive RLS has a ~0.1 attenuation-bias floor that averaging does
   not remove); fast channel = the mu belief, which remains the learned
   target. Sub-limit data is structurally mu-blind (utilization <= 0.4
   leaks zero; higher sub-limit utilization yields only a one-sided lower
   bound), so the mu channel cannot be trained from familiarization data.
   The eligible-cell list is frozen only after deciding whether family #2
   randomizes vehicle parameters (noise-cell matched prize compresses to
   ~0.12 with vehicle randomization on).
   **L4 (vehicle-class prior) scope**: measured upper bound = the vehicle
   share (<= 0.19; zero in noise cells), reachable by L3.5 familiarization
   in 5 s — a class prior can at most shorten the prefix. A minimal
   L4-prior arm (coarse kappa bins as RLS prior; within-class variance
   swept) rides along in WP1 as an exploratory arm, not a gated claim.
2. **Arms**: L0 current-frame; L2_window_25/50/100; L3_GRU (+ reset-eval
   control). Capacity matching counts non-input-projection parameters
   only; window arms use a shared per-frame encoder (72->h) + temporal
   pooling so the matched quantity is encoder+head. Compute-matched
   (same steps/samples); per-arm LR/epoch mini-grid selected on selection
   seeds only. Held-out mu points (off the 12-point grid) in evaluation to
   prevent grid memorization. >= 8 training seeds per arm; **primary arm =
   L3_GRU, pre-registered; all other arms exploratory** (no best-arm
   selection inference).
3. **Substitution test**: each estimator's reveal-tick output replaces
   true mu in the SAME scripted planner/seeker used by the regime
   measurement.
4. **Pre-registered criteria** (frozen before any run):
   - Anchors: **deployable-primary prize := matched VoI** (same-cell
     degraded oracle minus floor); **floor := best belief-free arm** (max
     over seeker variants and fixed plans, re-measured on the enlarged
     validation set); clean-anchor fractions reported, not gated on.
   - Eligible cells := cells with matched prize >= 0.15 on the re-measured
     panel (current 2-seed estimate: ~5-6 cells, all at reveal 9.5 m;
     the frozen list is fixed by the WP0.3 re-measurement before WP1 runs).
   - Validation set per cell: 12 mu x >= 20 disjoint validation seeds
     (>= 240 episodes); floor and matched oracle re-measured on the same
     enlarged set.
   - **Primary PASS** = L3_GRU recaptures >= 50% of the matched prize in
     >= 3 eligible cells, each with one-sided 97.5% CI of the
     paired-by-episode (arm - floor) difference excluding 0,
     seed-clustered robust SE over 8 training seeds. (Power at the
     smallest eligible cell ~ 80%+; the multiple-cell rule is conservative
     — family-wise false-positive ~ 1.6e-4 — so the risk direction is
     power, not false positives.)
   - Cross-cell aggregate (reported): pooled fraction =
     sum(arm - floor) / sum(prize) over eligible cells, episode-paired;
     per-cell fractions descriptive only.
   - Pre-registered outcome routes: "all arms fail" -> one excitation/
     representation iteration (<= 1 week, <= 4 h CPU), then accept the
     bound as a result; "L0 succeeds" -> leak audit, <= 1 redesign round,
     then report the leak itself as a finding and scope claims down.
5. **C3 variant (required for the C3 readout)**: mu-informative excitation
   confined to t < 1.0 s (scripted ramp-then-release behavior policy),
   then a sub-limit constant-speed segment with zero shortfall events
   lasting > (FIR window + max sensor delay) = 2.5 s, decision at
   t >= 3.5 s (extend deadline/initial distance as needed). Per-cell
   telemetry check: time of last shortfall event vs decision tick, gap
   > 2.5 s verified and reported. C3 readout = L3 vs L2_100 paired
   difference with CI, **reported only if at least one history arm clears
   the floor**; equivalence pre-registered via TOST (|delta| < 0.05, 90%
   CI inside the bounds -> "FIR-sufficient"); three-way verdict: IIR wins
   / FIR sufficient / indeterminate.

Budget: ~1 day code + supervised training minutes per run; full matrix
< 2 h CPU (enlarged validation adds minutes at ~0.036 s/episode). This
package replaces the cancelled 20-cell RL matrix as the learning gate.

### WP2 — Sequence proposal + verifier (C4 skeleton)

Revives the May horizon-output contract with the new foundations. New code
(largest engineering block of the plan): proposal head + demo format +
replan-loop runner + verifier module + recoverable-set query module.

1. **Proposal head**: short-horizon action sequence (H ~ 0.5-1.0 s,
   piecewise segments), trained by imitation of demos generated on demand
   by the scripted per-mu oracle ramp controller (no RL), conditioned on
   the WP1 belief estimate. DAgger-lite + held-out epoch selection are
   pre-required (the G1' BC-compounding lesson applies here, not to WP1).
2. **Verifier (privilege-free by construction)**: deterministic env copy
   with hidden parameters set to the *believed* envelope (WP1 estimator
   output) — never the true mu; the true sim is used only for outer
   evaluation. Lightweight alternative: the closed-form d_of_mu / v_dodge
   envelope checks from `ramp_policy_voi_regime.py` evaluated at the
   believed mu. Recoverable-set check: a new query module over the
   measurement-C grid with conservative interpolation (snap to the
   lower-mu, higher-speed neighboring cell; criterion save >= 0.75);
   "violations = 0" is claimed against this conservatively gridded
   surface. If WP6.1 promotes a merged v4/v5 controller, the verifier
   binds to the merged controller's re-measured boundary (see WP6.1);
   family-#2 use requires re-running measurement C on that family
   (budgeted in WP0/WP2, ~30 min CPU).
3. **Acceptance**: stack >= belief-free stack everywhere (no clean-regime
   regression) and captures >= the WP1 fraction in degraded tight windows;
   verifier veto and false-veto rates reported; **adversarial wrong-belief
   stress test**: feed deliberately wrong mu beliefs (+/-0.3, directional
   over-estimates) — hard-safety failures must remain 0 (verifier + reflex
   bound the harm); **real-time budget report**: per-tick rollout
   wall-clock at 50 Hz replanning, claim scoped to the single-track-model
   verifier. <= 1 repair round if acceptance fails, then G-C adjudicates
   as-is.

Budget: ~2-3 engineering days + ~1-2 h CPU evaluation.

### WP3 — Guarded end-to-end refinement (optional, last)

Only if WP1+WP2 pass and a measurable gap to the matched oracle remains:
m1087 staged chain (BC warm-start from the WP2 stack -> capability
pretrain with the envelope head -> guarded RL, 1024-step smoke first),
with the P1 reward residual explicitly cited and the WP1 substitution
metric (not return) as the gate. Stop rule: any washout of the WP1-level
belief metric blocks promotion.

### WP4 — High-fidelity spot checks (after WP0 and after WP2)

Minimal cell set: {9.5 m x clean, 9.5 m x 100 ms delay, 9.5 m x noise
0.05} on the Chrono backend. Preconditions: a smoke check of the M3214
wrapper x chrono_backend_worker composition (never exercised together);
per-cell detector tau re-calibration (Chrono shortfall noise floor
differs); the per-mu oracle controller is migrated, so the readout is
"plan migratability + regime direction", declared as such. Acceptance:
VoI sign/ordering direction preserved per cell. If direction is not
preserved -> claims scoped to low-fidelity sim and papers state it.
Budget: re-estimated from measured Chrono throughput after the smoke
check (not "~1 command").

### WP-RL — C5 program (priced first, trained second)

1. **Pricing (zero training; S0-S3 completed, A1 lateral rider completed, A3
   C5' target consolidation completed)**: the reflex degradation curve —
   spread tiers S0 nominal / S1 current (+-20%, what v4 was tuned on) /
   S2 extended (mass 0.70-1.50, brake/drive 0.60-1.30, stiffness
   0.50-1.50, tau to 2.5x) / S3 adversarial corners, at two limit-demand
   tiers (T-mid feasible avoidance; T-limit near the per-instance
   feasibility edge, infeasible rows excluded from the denominator).
   **S4 passenger-car-population tier (required extension after the S0-S3
   pricing report)**: direct VehicleParams construction over the fleet
   envelope — mass ~0.6-2.2x nominal (~900 kg-3.2 t), wheelbase/lf/lr
   and Iz beyond the sampler's default ranges, CG and authority spreads
   to match vehicle classes — with per-instance feasibility relabeling
   and per-instance oracles; the S0-S3 run prices the within-model rungs
   and S4 prices the population claim itself.

   Live disposition (2026-06-12, M3222): S0-S3 rejected the original spread
   formulation, and the cheap current-sim A1 lateral rider over cg/Iz also
   rejected the spread mechanism (0/4 cells qualified; S4L/T-limit prize
   +0.007 CI95 [-0.014, +0.028]). M3222 then confirmed the C5' structural
   ceiling target on fresh C5-F1 T-limit seeds by the frozen A3 rule: 3/4
   cells qualified, with S1/S2/S3 oracle-minus-pertuned gaps
   +0.1597/+0.2153/+0.1736 and CI95 lower bounds > 0; S0 was positive but
   below the +0.15 bar (+0.1389). The Chrono variant-selector connector is
   implemented and smoke-tested, but any S4-HF-lite pricing execution still
   needs a frozen preregistration and a declared handling of the unmapped
   continuous `lf/lr/Iz/cf/cr` lateral/tire channels. M3221 completed the
   obs-normalization audit and found a blocker; M3224 implemented and smoked
   an explicit 36 m/s profile (`vx/40`, `vy/40`, `ax/50`, `ay/60`,
   `road_y/60`, `rel_vy/30`, 2.5 s preview), closing the high-speed
   env-contract blocker for that profile only. Population training still
   needs its own preregistered profile/floors, and Track C remains blocked
   until CP-1.
   Four paired arms: fixed v4 / v4+RLS-retuned (the classical
   identification arm reviewers will demand) / per-instance-tuned v4
   (the "tune every car" upper bound, quantified to show its cost) /
   per-instance privileged oracle (ceiling). Frozen go-criteria: >= 2
   cells with (per-tuned - fixed) >= 0.15 CI-excluding-0 AND
   (per-tuned - RLS-retuned) >= 0.08; otherwise C5 is honestly rejected
   ("classical identification suffices") and recorded.
2. **RL training (only if priced)**: m1087 staged chain (BC warm-start
   from per-instance oracle demos -> capability pretrain -> guarded RL),
   reward recalibration 40/60 as measured, held-out epoch selection;
   trained across the spread, judged purely on outcomes against the four
   arms on frozen validation seeds. The G1 variance lessons apply; the
   measured prize sets the effect-size prior.
3. **Declared sim limits**: tire-curve shape (tanh) is fixed and there is
   no load transfer — season/modification diversity is proxied by
   parameter spread only; stated in the papers' limitations.
4. **Sampling design is governed by the coverage map**
   (`docs/data-coverage-map-2026-06.md`): training-data distribution for
   C5 is designed against the audited gaps, in priority order —
   (i) S4 population tier + **obs-normalization implementation after the
   M3221 audit** (B2 high-speed profile implemented in M3224; any population
   variant still needs explicit preregistration); (ii) moving obstacles (B1
   env engineering complete in M3223, outcome panels still unpriced);
   (iii) > 20 m/s speed domain (B2 env engineering complete in M3224,
   outcome panels still unpriced); (iv) geometry-channel degradation (B3 env
   engineering complete in M3225, outcome panels still unpriced) and split-mu
   (M3225 audited as not expressible in current-sim); (v) minute-scale drive
   structure (the real L3.5 scale). Items
   (ii)-(v) are env-engineering
   prerequisites scheduled before the corresponding training claims, not
   after.

### WP5 — Papers

- **Paper A (science)**: "When does a driving policy need to know its own
  limits?" — VoI framework, driver mechanism, two-regime law, C2/C3
  results, with the negative-result arc as the motivating spine.
  Related-work positioning (pre-committed): RMA/UP-OSI-style online
  adaptation (our clean-regime null is their success case; the degraded
  regime is their measured failure boundary), HJ-reachability/CBF safety
  filters (the recoverable-set check as an empirically certified
  analogue), and the autonomous-drifting RL line indexed in
  `docs/m7-related-papers.md` (DOA, Cai RA-L 2020, Hoshino ITSC 2024).
  Target: **RA-L (primary, submit by 2026-08-15)**, IV/ITSC 2027 as
  conference fallback. Priority over Paper B.
- **Paper B (systems/process case study)**: 3200+ milestone autonomous
  research loop + manual takeover methodology (feasibility oracles,
  ignition gates, pre-registration, failure taxonomy: bookkeeping loops,
  agent-session-bound compute, plausible-but-wrong repair branches).
  Acceptance: outline passes one external-reader test; every failure
  class evidenced by >= 2 milestones. Target: arXiv + workshop; finalize
  may slip behind Paper A.
- Authoring stack: the ARS skills (academic-pipeline / academic-paper /
  academic-paper-reviewer / deep-research) installed 2026-06-11; internal
  review via academic-paper-reviewer before any submission.

### WP6 — Process and stack housekeeping

0. Commit this plan + keep thesis/plan as the Phase-2 anchor (week-1,
   first action).
1. **v5 promotion decision packet** (data complete: +2 rows / 0
   regressions vs deep-overshoot liability; recommendation: promote only
   with a deep-slip yield-to-v4 arbitration clause). **If promoted, before
   WP2 consumes any recoverable-set surface: re-run (a) the recovery
   panel, (b) the fixed feasible-row panel, (c) the fresh-seed panel on
   the merged controller; the WP2 verifier binds to the merged
   controller's re-measured boundary.** If not promoted, WP2 binds to the
   v4 surface as measured.
2. Loop guardrails before any autonomous restart: pre-repair feasibility
   oracle gate; blocked-dependency escalation hook; managed-process rule
   for long measurements (the agent-dies-measurement-dies pattern occurred
   3x); explicit paused/archived semantics for
   `research_queue.csv`/`research_status.json`/`scoreboard.csv` during
   takeover.
3. **week-1 item**: keep `docs/current-status.md` as the compact live
   ledger for takeover/Phase-2 state with thesis/plan links; keep the
   feasibility-audit README current as the script -> artifact -> doc
   measurement index.

## 5. Schedule (calendar; CPU budgets firm, calendar may slip on design
iteration rounds)

| week | packages | compute |
|---|---|---|
| 1 | WP0 engineering (wrapper modes) + family-#2 design freeze + clean acceptance; WP6.0/6.1/6.3 | ~2 h CPU |
| 2 | WP0 degraded sweeps + hardening + bridge test; WP1 code; Paper B outline | ~4 h CPU |
| 3 | WP1 full matrix + report; WP4 spot check #1; Paper A skeleton | ~3 h CPU |
| 4 | WP2 build + evaluate (largest engineering block) | ~2 h CPU |
| 5 | WP2 finish / WP3 smoke (optional); WP4 spot check #2 | ~2 h CPU |
| 6+ | Paper A to draft-complete (priority); Paper B finalize may slip | writing |

GPU requirement: none expected (CPU-bound measured); WP3 optional smoke
only.

## 6. Decision gates and stop rules

- G-A (after WP0): law replicated on family #2? yes -> WP1; no -> re-scope
  papers to family-specific, still run WP1 on family #1.
- G-B (after WP1): primary PASS? yes -> WP2; "all arms fail" -> one
  bounded iteration then accept the bound; "L0 succeeds" -> leak audit,
  <= 1 redesign round, then report the leak as a finding.
- G-C (after WP2): stack dominates belief-free everywhere? yes -> WP3
  optional + papers claim C4; no -> <= 1 repair round, then report the gap
  and scope papers to C1-C3.
- Global: criteria pre-registered before every run; long jobs as managed
  background processes only; selection/validation/training seed streams
  mutually disjoint and frozen in pre-registration JSONs.

## 7. Risks

| risk | mitigation |
|---|---|
| Regime law family-specific | WP0 family #2 first; refutation is a result |
| Estimator leaks via training distribution (speed-register lesson) | mu-decoupled behavior policy + dataset probe R^2 <= 0.1 gate (linear + MLP probes) |
| Eligible-cell prizes shrink on re-measurement | eligible list frozen only after WP0.3 hardening; criteria reference the re-measured panel |
| BC compounding (G1') | DAgger-lite + held-out epoch selection in WP2 (imitation); WP1 is pure supervised estimation (not applicable) |
| Capacity/compute confounds in C3 | encoder+head matching rule, compute matching, TOST equivalence bounds, conditional readout |
| Knife-edge cells destabilize comparisons | jitter + >= 10 validation seeds + Wilson CIs on all main-table cells |
| Sim-fidelity overclaim | WP4 spot checks with declared migration scope; deployability claim-boundary section; absolute numbers never claimed |
| Verifier privilege contamination | believed-parameter-only verifier, true sim only for outer eval |
| Process: measurements die with agent sessions | managed background processes only (WP6.2 rule) |
| P1 reward residual weakens future RL | WP3 gated on the WP1 substitution metric, not return; BC warm-start mandatory |
