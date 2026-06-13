# Current Status

This file is the compact official state for the project. Milestone documents
and `docs/research-log.md` remain the detailed log of the autonomous-harness
era; the Phase-2 plan and thesis (pointer table below) define the active
program. Last full refresh: 2026-06-14 (the 2026-06-11 WP6.3 refresh
replaced the stale paper-route state; this update folds in M3215-M3260,
the C5 pricing disposition, the S4-HF-lite backend connector/pricing work,
WP6.2 guardrails, the A1 lateral-channel rider, the A2 obs-normalization
audit, the A3 C5-prime target consolidation, B1/B2/B3/B4 env-engineering
smokes, D1 Chrono pricing, the first C1 warm-start failure/localization, the
D1b Chrono-native oracle protocol smoke plus full direction-pricing panel,
the C1 v2 tail-balanced quick-smoke negative, the M3233 C1
synthesis/repricing pivot, M3234 C1 admission-interface pricing, M3235 C1
tail-family interface smoke, the M3236 tail-family interface pretrain quick
negative, the M3237 C1 interface synthesis/repricing pivot, and the M3238
C1 family-selector repricing negative, the M3239 B1b moving-obstacle
pricing protocol smoke, the M3240 full B1b moving-obstacle pricing
negative, the M3241 B2b high-speed pricing protocol smoke, the M3242
full B2b high-speed pricing negative, the M3243 PI/new-route escalation,
the M3244 C1-v3 residual-RL smoke, the M3245 C1-v3 residual-RL
stage-1 negative, the M3246 C1-v4 distillation Stage-A pass, and the M3247
C1-v4 guarded-RL first-rung failure that closes Track C, the M3248
Phase-4 E0 Chrono spread expressibility audit that opens E1, the M3249
E1 quick protocol smoke, the M3250 full E1 spread-revival pricing
negative, the M3251 E2 Chrono two-regime protocol smoke, the M3252
full E2 Chrono two-regime verdict, the M3253 E3 measurement-A/C
protocol smoke, the M3254 E3 tire-truth telemetry connector smoke, the
M3255 full E3 Chrono measurement A/C verdict, the M3256 blocked CP-3
Track-F PI checkpoint, the M3257 E3-fix detector-onset reconciliation, the
M3258 E2' hardened two-variant clean-flip confirmation, the M3259 E1'
oracle-adequate spread-revival repricing negative, and the M3260 E4
drift-regime pricing panel).

## Project Identity

- Repository: `general-evasive-driver`
- Python package: `autodrift`
- Working title: General Evasive Driver
- Core direction (Phase-2): capability-boundary tracking — when and how a
  driving policy at the handling limit needs a belief about its own
  capability envelope, on top of a certified reflex safety layer
  (the two-regime law).

## Project State: manual-takeover Phase-2

History in one paragraph: the autonomous harness loop ran through M3214
before manual takeover; the manual takeover has since registered
M3215-M3260. `experiments/research_status.json` now records
3260 completed / 7 failed / 4 blocked task entries, with `next_task:
null`. On
2026-06-11 an independent feasibility audit showed the M3108–M3212
residual-repair branch was repairing physically unsolvable rows, and the
session was taken over manually (M3213 blocked;
`docs/feasibility-takeover-2026-06-route-decision.md`). The takeover route
then certified the reflex layer at the physical ceiling: oracle
certification measured all 7 residual hard-safety rows unrepairable by any
controller, causal or privileged (43,372 privileged rollouts, 7/7 hard-fail
in both tiers, `docs/feasibility-audit-oracle-certification-2026-06.md`);
feasible-row success is 55/55 on the fixed panel and 162/165 = 98.2% pooled
aeb_feasible with 0 collisions on all 172 feasible fresh-seed episodes
(`docs/feasibility-audit-stratified-panel-2026-06.md`); the HF4 dual-backend
measurement found 249/256 identical outcomes under Chrono::Vehicle with zero
new hard-safety failures
(`docs/feasibility-route-hf4-full-discrepancy-2026-06.md`). The ~1500-
milestone self-ID question was reformulated as capability-boundary tracking
(`docs/capability-boundary-tracking-thesis-2026-06.md`) and measured to the
**two-regime law**: under clean sensing, VoI(belief) = 0.000 at every reveal
window 9.5–30 m — a belief-free threshold-seeker matches the per-mu oracle;
under degraded sensing (delay/noise on the ego channels), belief value
revives to 0.17–0.88 in 12/14 cells (11/14 against the best belief-free
arm). Phase-2 (`docs/research-plan-phase2-capability-boundary-tracking.md`,
v2) started 2026-06-11 to test the law's generality (C1), belief
learnability (C2), FIR-vs-IIR (C3), and the deployable
belief→verifier→reflex stack (C4).

## Program Progress Ledger (refresh 2026-06-14)

Claims:

| claim | status | verdict artifact |
|---|---|---|
| C1 generality of the two-regime law | **family-specific scope** (G-A FAIL per pre-registration): family #2 replicates the clean half (VoI +0.025) but its degraded revival is mode-dependent — noise-type degradation revives belief everywhere, delay-type stays ~0 because the drive-ramp seeker identifies ~1 s before commitment. The noise-buys-delay bridge was falsified on its pre-registered double criterion. | `docs/m3215-wp0-degraded-sweep-bridge-validation.md` |
| C2 belief learnability | **terminal bound accepted** (G-B FAIL, the single authorized iteration consumed): belief is learnable — the project's first working history-borne capability estimator (GRU R^2 0.91-0.99, reset-control-destroyed, window arms at predict-the-mean) — but not monetizable through the substitution interface; the bounded iteration was stopped by the leak gate because on-policy closed-loop data is necessarily single-frame mu-readable (the thesis Section-10 capstone). delay12 +0.185 (lower bound +0.110) remains the only substitution-level positive. | `docs/m3216-wp1-modular-belief-experiment.md`, `docs/m3217-wp1-belief-substitution-bounded-iteration.md` |
| C3 FIR vs IIR | **not adjudicated** (pre-registered condition not triggered: no history arm cleared the floor) | M3216 doc |
| C4 deployable stack | **closed** (WP2 never opened per G-B) | plan Section 2 |
| C5 one policy for all passenger cars (RL as engineering) | **spread formulation rejected by pricing**. S0-S3 mass/brake/drive/tau spread failed its pre-registered bar (0/8 cells): the fixed reflex's degradation curve was flat, per-instance grid tuning had nothing to buy, and kappa-RLS retuning self-harmed at corners. M3220 then gave the final cheap current-sim lateral-channel rider (cg/Iz S4L): 0/4 cells qualified; S4L/T-limit prize was only +0.007 with CI95 [-0.014, 0.028]. **Measured current-sim survivor (C5' candidate): the reflex structural ceiling gap. M3222 fresh-seed A3 consolidation confirmed the C5-prime target by the frozen rule: 3/4 T-limit cells qualified with oracle - per-tuned gaps +0.1597 to +0.2153 and CI lower bounds > 0; S0 was positive but below the +0.15 effect-size bar (+0.1389).** M3218/M3219 completed the Chrono connector inventory + selector smoke. M3227 then ran the preregistered S4-HF-lite multi-vehicle direction-pricing proxy on frozen A3 structured-gap rows and found the direction **reversed in all three Chrono variants**: structured current-sim oracle-tail replay underperformed `v4_pertuned` on Sedan, BMW_E90, and UAZBUS. M3230/M3231 then re-priced the high-fidelity direction with native Chrono oracle search and found it direction-positive on Sedan (+0.2222) and BMW_E90 (+0.1111), satisfying the CP-2 direction precondition. The local C1 imitation chain then failed and pivoted repeatedly: M3228/M3232 direct MLP BC failed action-MSE gates, M3229 localized tail-action generalization, M3233 pivoted, M3234/M3235 priced and smoked a structured tail-family interface, M3236 failed rare-family pretraining, M3237 pivoted again, and M3238 rejected the local family selector. M3243 recorded that blocked dependency; PI reopened C1 as C1-v3, residual RL over frozen v4 with no supervised oracle imitation. M3244 proved the residual route runnable at 1024-step smoke scale. **M3245 then ran the preregistered C1-v3 stage-1 and failed the frozen gate: 0/3 cells passed, v4+residual minus `v4_pertuned` was -0.6276/-0.4262/-0.3299 on S1/S2/S3, and all CI95 intervals were negative. PI then opened C1-v4 as the final distill-then-RL route. M3246 passed the frozen Stage-A distillation gate, but M3247 failed the Stage-B guarded-RL first rung: 0/3 cells passed, 0/3 cells met the extension movement threshold, and `v4_stage_b - v4_pertuned` was -0.0651/-0.0425/-0.0052 on S1/S2/S3.** No 4M extension, C2, C3, scale-up, driver-performance, high-fidelity sufficiency, repair-success, feasibility-proof, paper, or self-ID claim is admitted; Track C is closed absent new pricing evidence. | `docs/c5-reflex-degradation-2026-06.md`, `docs/m3220-a1-s4-lateral-spread-rider-pricing.md`, `docs/m3222-a3-c5prime-target-consolidation.md`, `docs/m3219-s4-hf-lite-chrono-variant-selector-smoke.md`, `docs/m3227-d1-s4-hf-lite-chrono-pricing.md`, `docs/m3228-c1-c5prime-oracle-demo-bc-warmstart.md`, `docs/m3229-c1-bc-warmstart-failure-localization.md`, `docs/m3230-d1b-chrono-native-oracle-pricing-smoke.md`, `docs/m3231-d1b-chrono-native-oracle-pricing-full.md`, `docs/m3232-c1-v2-tail-balanced-warmstart-smoke.md`, `docs/m3233-c1-synthesis-repricing.md`, `docs/m3234-c1-admission-interface-pricing.md`, `docs/m3235-c1-tail-family-interface-smoke.md`, `docs/m3236-c1-tail-family-interface-pretrain-quick.md`, `docs/m3237-c1-tail-family-interface-synthesis-repricing.md`, `docs/m3238-c1-family-selector-repricing.md`, `docs/m3244-c1-v3-residual-rl-smoke.md`, `docs/m3245-c1-v3-residual-rl-stage1.md`, `docs/m3246-c1-v4-distill-stage-a.md`, `docs/m3247-c1-v4-stage-b-guarded-rl.md` |

Phase-4 Track E addendum: M3248 E0 **completed / passed**. All three
whitelisted Chrono variants (`sedan_tmeasy`, `bmw_e90_tmeasy`,
`uazbus_tmeasy`) reset/stepped with finite obs72 and matching backend_info.
The frozen spread-axis table admits E1 on selected vehicle fixtures with
load-transfer physics active, while blocking independent payload-position,
h_cg, tire-family, split-mu, and continuous lf/lr/Iz/cf/cr axes without new
connectors (`docs/m3248-phase4-e0-chrono-spread-expressibility-audit.md`).
M3249 E1 quick protocol smoke **completed / passed**: Sedan/BMW_E90/UAZBUS
all exercised fixed*, RLS-retuned, per-instance tuned, and native-oracle rows;
native oracle ran structured and CEM candidates per variant. M3250 E1 full
pricing then **completed / negative by the frozen rule**: 0/3 variants
qualified, pooled `v4_pertuned - fixed_star` was -0.0556 with CI95
[-0.1667, 0.0], pooled `v4_pertuned - v4_rls` was 0.0000 with CI95
[-0.1667, 0.1667], and the attempt-limited native-oracle anchor was below
`v4_pertuned` in this panel (-0.4444, CI95 [-0.6667, -0.2222]). E1 did not
admit Track F (`docs/m3250-phase4-e1-spread-revival-pricing-full.md`).
M3251 E2 Chrono two-regime protocol smoke **completed / passed**: 18/18
expected quick rows were written on the Sedan fixture, covering clean reveal
9.5 m and 30 m plus a delay25 tight degraded spot with oracle_ramp,
threshold_seeker, and fixed_ramp arms; reset obs finite, variant match, and
non-verdict gates all passed. Quick indicative readouts are not a two-regime
law verdict (`docs/m3251-phase4-e2-chrono-two-regime-smoke.md`). M3252 then
ran the full frozen E2 Sedan/TMeasy panel and returned a **positive clean
Chrono belief-value verdict**: 280/280 selection rows and 192/192 validation
rows were written, all protocol gates passed, and clean oracle - best-floor
qualified at reveal 9.5 m (+0.75, CI95 [0.375, 1.0]) and 12 m (+0.625, CI95
[0.25, 0.875]). The delay25_tight spot is secondary only (+0.125, CI95
[0.0, 0.375]); Track F remained blocked pending E3 plus CP-3, and now remains
blocked on CP-3 after M3255 (`docs/m3252-phase4-e2-chrono-two-regime-full.md`).
M3253 E3 measurement-A/C protocol smoke **completed / passed**: 4/4 expected
quick rows were written on the Sedan/TMeasy fixture, reset obs were finite,
variant matching passed, and quick mode stayed non-verdict. Measurement A
rows produced obs72 detector traces for long and lateral ramps
(fired_step 50 and 125); measurement C rows produced planar overshoot
recovery traces for baseline_coast and v4_incumbent (recovered at steps 9
and 11). M3253 does not decide Chrono detection latency, the full recoverable
set, or Track F admission; full E3 still needs a separate preregistration
with frozen truth definitions, cells, seed streams, paired readouts, and
safety-gating thresholds (`docs/m3253-phase4-e3-chrono-measurement-ac-smoke.md`).
M3254 E3 tire-truth telemetry connector smoke **completed / passed**: 8/8
expected samples and 32/32 wheel rows were written on the Sedan/TMeasy
fixture, obs72 stayed finite, every sample exposed four tire-telemetry rows,
wheel numeric fields were finite, and normal loads were positive
(3195.13-4952.06 N). M3254 does not decide full E3 or Track F; it only
confirms that full E3 can now preregister Chrono tire-truth definitions
instead of relying on obs72-only traces
(`docs/m3254-phase4-e3-chrono-tire-telemetry-smoke.md`). M3255 then ran the
full frozen E3 Sedan/TMeasy measurement A/C panel and **completed / passed**
all protocol gates: 24/24 detector-latency rows and 72/72 recovery-budget
rows were written, obs72 stayed finite, variant and telemetry gates passed,
truth onsets were observed in all measurement-A rows, and Track F remained
not admitted. Measured safety readouts: detector miss rate 0.1667, p90
latency 1.346 s, early-fire rate 0.5, v4 recovery 1.0, baseline recovery
1.0, and v4-baseline recovery delta 0.0 across the frozen overshoot panel.
M3255 marks the Track-E Sedan/TMeasy evidence package ready for PI CP-3
review, but does not self-approve Track F, driver-performance, full
high-fidelity sufficiency, paper, feasibility-proof, repair-success, or
self-ID claims (`docs/m3255-phase4-e3-chrono-measurement-ac-full.md`).
M3256 records the resulting process blocker as a **blocked** CP-3 gate row:
Track F F1/F2/F3 remain blocked until PI records a CP-3 disposition approving
targets and GPU-days budget, rejecting Track F, or requesting a concrete
additional preregistered unit. The escalation note is
`docs/escalations/2026-06-13-phase4-cp3-track-f-pi-checkpoint.md`; this is
not a training, promotion, performance, paper, feasibility-proof, or self-ID
claim. PI then recorded CP-3 disposition A in that escalation: harden Track E
before any GPU budget. M3257 E3-fix **completed / passed** the detector-onset
reconciliation: 24/24 Measurement-A case rows and 3426 trace rows were written,
all protocol gates passed, original early-fire rate was 0.5, reconciled
early-fire rate was 0.0, detector miss rate stayed 0.1667, corroborated
early-fire rate was 0.5, uncorroborated detector-fire rate was 0.0, and the
reconciled p90 latency remained 1.346 s. The reconciled rule treats an obs72
detector fire as actor-visible onset when later corroborated by the frozen
M3255 tire-slip event inside the preregistered 150-step window; otherwise the
M3255 tire-slip onset is retained
(`docs/m3257-phase4-e3-detector-onset-reconciliation.md`). M3258 E2'
hardening then **completed / confirmed the clean flip** under the frozen
CP-3 disposition-A protocol: 560/560 selection rows and 5760/5760 validation
rows were written, with 30 validation seeds per cell on Sedan/TMeasy and
UAZBUS/TMeasy. All five clean reveal tiers qualified on both variants;
the frozen tight-cell criterion passed with 4 positive tight cells across the
two variants, max clean oracle-minus-floor was +0.7667, and Track F remained
not admitted. Track F is now blocked only on the later PI GPU-days checkpoint;
E1' spread-revival repricing remained a separate Track-E' unit
(`docs/m3258-phase4-e2prime-chrono-two-regime-hardening.md`). M3259 E1'
oracle-adequate repricing then **completed / rejected spread revival** under
the frozen rule: protocol gates passed, the selection-row oracle-adequacy
gate passed on Sedan/BMW_E90/UAZBUS, validation used 24 units per variant,
and 0/3 variants qualified. Pooled `v4_pertuned - fixed_star` was -0.1389
with CI95 [-0.2222, -0.0556], pooled `v4_pertuned - v4_rls` was -0.0833
with CI95 [-0.1806, 0.0139], and pooled `native_oracle - v4_pertuned` was
+0.1806 with CI95 [0.0972, 0.2778]. Track F remains blocked until the later
PI GPU-days checkpoint; M3259 makes no training, driver-performance,
high-fidelity sufficiency, paper, feasibility-proof, repair-success,
robustness-result, or self-ID claim
(`docs/m3259-phase4-e1prime-spread-revival-repricing.md`).
M3260 E4 drift-regime pricing then **completed / priced the
beyond-saturation regime** under frozen low-mu Chrono cells: 204 total rows,
44 selection rows, and 160 validation rows were written; all protocol gates
passed; selection-row oracle adequacy passed; each drift cell used 20
validation units. The `low_mu_power_oversteer` cell had oracle - fixed* and
oracle - tuned-reflex = +0.4000 with CI95 [0.1797, 0.6203], driven by the
drift-specialized oracle (0.40 success) while fixed* and tuned reflex were
0.00; reflex failures were mostly fail-to-enter (34) plus fail-to-stabilize
(6). The `lift_off_recovery` cell was near-neutral: oracle - fixed* and
oracle - tuned-reflex = +0.0500 with CI95 [-0.0480, 0.1480], with reflex
failures all fail-to-stabilize. M3260 does not admit Track F/F2, training,
driver-performance, high-fidelity sufficiency, paper, feasibility-proof,
repair-success, robustness-result, or self-ID claim
(`docs/m3260-phase4-e4-drift-regime-pricing.md`).

Work packages: WP0 **complete** (wrapper modes M3215-validated, family #2
frozen with clean acceptance after one pre-registered repair, statistical
hardening, governance refresh); WP1 **terminal** (M3216/M3217); WP2/WP3
**closed by gates**; WP-RL S0-S3 spread pricing **completed / original C5
rejected**, A1 lateral-channel rider **completed / negative**, A3 C5-prime
target consolidation **completed / target confirmed; CP-1 conditionally approved**, S4-HF-lite
connector **completed / selector smoke passed**, D1 Chrono multi-vehicle
direction-pricing **completed / negative** (all three variants reversed for
structured current-sim oracle-tail replay), CP-1 **conditionally opened C1**,
C1 first warm-start attempt **failed** (M3228), M3229
**localized the failure** to selection/validation tail-action generalization,
M3232 v2 rare-tail-balanced quick smoke **failed** the unchanged action-MSE
gate (0.291470 vs <=0.12; demo replay/checkpoint/dataset succeeded),
M3233 C1 synthesis/repricing **completed / pivot** (C5-prime target still
priced, but local direct-MLP/action-MSE warm-start branch closed), M3234 C1
admission-interface pricing **completed / positive** (tail-family quick smoke
priced, no full training or C2 admission), M3235 C1 tail-family interface
smoke **completed / passed** (exact target reconstruction, no policy checkpoint),
M3236 C1 tail-family interface pretrain quick **failed** (rare-family collapse;
route to synthesis/repricing before more local pretraining), M3237 C1
tail-family interface synthesis/repricing **completed / pivot** (close local
frame-wise pretraining), M3238 C1 family-selector repricing **completed /
negative** (best row selector clears aggregate accuracy but fails rare-family
and reconstruction gates; local selector/interface training blocked pending PI
or new nonlocal-interface pricing), M3243 PI/new-route escalation **recorded /
resolved by PI route decision** (C1-v3 residual RL on frozen v4), M3244 C1-v3
residual-RL smoke **completed / passed** (1024 steps, all quick gates true,
checkpoint/metrics written), M3245 C1-v3 residual-RL stage-1 **completed /
failed frozen gate** (0/3 cells passed; v4+residual minus `v4_pertuned`
-0.6276/-0.4262/-0.3299 on S1/S2/S3 with all CI95 intervals negative; no
scale-up, C2, C3, or claim admission), M3246 C1-v4 distillation Stage A
**completed / passed** (primary student minus `v4_pertuned`
+0.0139/-0.0208/+0.0000 in S1/S2/S3; all cells within -0.05; Stage B
guarded RL admitted only after separate preregistration), M3247 C1-v4 Stage B
guarded RL **completed / failed** (0/3 pass cells, 0/3 movement cells;
`v4_stage_b - v4_pertuned` -0.0651/-0.0425/-0.0052; no 4M extension and
Track C closed),
D1b
Chrono-native oracle protocol smoke **passed** (M3230), and D1b full
direction-pricing **completed / positive** (M3231: Sedan +0.2222,
BMW_E90 +0.1111; CP-2 D1b precondition satisfied);
A2 obs-normalization audit **completed / blocker found**
(`road_y/20`, high-speed ego speed/accel, and obstacle `rel_vy/12` require a
follow-up normalization/preview implementation before population or high-speed
training); B1 moving-obstacle env axis **completed / smoke passed** (flagged
constant-velocity crosser, dynamic labels, deterministic replay, legacy
zero-relvel preserved); B1b moving-obstacle pricing **completed / negative**
(M3239 passed the protocol smoke; M3240 full panel rejected the current
moving-crosser formulation with 0/4 cells qualifying, oracle-minus-pertuned
gap 0.0000 in every cell, oracle solvability 1.0, and fixed_star/v4_rls/
v4_pertuned all succeeding 32/32; all rows were `aeb_feasible`); B2
high-speed env axis **completed / smoke passed**
(explicit 36 m/s profile, selected-channel max abs 0.900, 2.5 s road preview,
high-speed labels 592/592; env-contract only, no training admission); B2b
high-speed pricing **completed / negative** (M3241 passed the protocol smoke;
M3242 full panel rejected the current high-speed formulation with 0/6 cells
qualifying, oracle solvability 1.0, oracle-minus-pertuned gap 0.125 in two
cells and 0.0000 in four cells, all paired CI95 lower bounds 0, and
scale-aware fixed_star/v4_pertuned succeeding 46/48 versus raw incumbent
42/48; weak high-speed pockets and scale-adapter transfer effects were
measured, but no priced type-(b) window-compression prize was admitted); B3
geometry-channel degradation **completed / smoke passed** (config-gated road
boundary plus active-obstacle continuous-channel noise, 16 episodes / 400
paired frames, ego/command and present/size/empty-slot channels unchanged,
deterministic replay 4/4; split-mu recorded as not expressible in the current
`DriftObstacleEnv` single-track outcome path); B4 minute-scale drive structure
**completed / smoke passed** (4 full seeds reached 3000 steps / 60.0 s,
warmup gate passed at steps 215-216, emergency obstacle appeared at step 250,
raw pass recorded at steps 991-999, minimum post-pass continuation 2001 steps,
deterministic replay 2/2; env-contract only, no controller outcome claim); WP4 spot
checks **partially updated**
(Chrono outcome coverage now includes D1 Sedan/BMW_E90/UAZBUS direction
pricing plus D1b Sedan/BMW_E90 native oracle direction-pricing, M3248
freezes the Phase-4 E0 expressibility envelope for Sedan/BMW_E90/UAZBUS,
M3252 gives the initial full E2 two-regime-law verdict on Sedan/TMeasy,
M3258 hardens E2' across Sedan/TMeasy and UAZBUS/TMeasy with 30 validation
seeds per cell and confirms the clean flip, M3259 completes E1' spread
repricing across Sedan/BMW_E90/UAZBUS with 24 validation units per variant
and 0/3 qualifying variants, M3260 adds a Sedan/TMeasy E4 drift-regime
pricing panel with 20 validation units per drift cell, and M3255 gives a full
E3 detector-latency/recovery-budget verdict on Sedan/TMeasy only. It still
does not cover UAZBUS D1b native search, non-Sedan E3, independent
payload-position/h_cg, tire-family, split-mu, continuous lateral/tire channel
mapping, or learned-policy outcome panels); WP5 papers
**pending**
(scope fixed: family-scoped mode-dependent two-regime law + estimator
positive + the capstone bound; plus C5' only if PI accepts the structural
ceiling route as a priced-but-not-converted negative); WP6 **current guardrails live** (6.0/6.1/6.2/6.3 done;
validator V7, escalation protocol, and managed-run helper are merged).

Harness ledger: M3215, M3216, M3217, M3218, M3219, M3220, M3221, M3222,
M3223, M3224, M3225, M3226, M3227, M3228, M3229, M3230, M3231, M3232, M3233, M3234, M3235, M3236, M3237, M3238, M3239, M3240, M3241, M3242, M3244, M3245, M3246, M3247, M3248, M3249, M3250, M3251, M3252, M3253, M3254, M3255, M3257, M3258, M3259, and M3260 registered and
executed through the harness (research-validate passed in pending and
completed states;
M3228 failed its full gate, M3229 completed, M3230 completed after a
same-turn rerun tightened the quick gate to require both structured and CEM
candidate coverage, M3231 completed after one infrastructure retry with
resume cleanup, M3232 failed the revised C1 v2 quick behavior gate, M3233
completed the C1 synthesis/repricing pivot, M3234 completed positive
admission-interface pricing, M3235 completed the no-PPO tail-family
interface smoke, M3236 failed the supervised tail-family pretrain quick,
M3237 completed the interface synthesis/repricing pivot, M3238 completed
the family-selector repricing negative, M3239 completed the B1b
moving-obstacle pricing protocol smoke, M3240 completed the full B1b
moving-obstacle pricing negative, M3241 completed the B2b high-speed pricing
protocol smoke, M3242 completed the full B2b high-speed pricing negative,
M3244 completed the C1-v3 residual-on-frozen-v4 PPO smoke, M3245
completed the C1-v3 stage-1 negative, M3246 completed the C1-v4
distillation Stage-A pass, and M3247 completed the C1-v4 Stage-B first-rung
negative, M3248 completed the Phase-4 E0 Chrono spread expressibility
audit, M3249 completed the E1 quick protocol smoke, M3250 completed the
full E1 spread-revival pricing negative, M3251 completed the E2 Chrono
two-regime protocol smoke, M3252 completed the full E2 Chrono two-regime
pricing verdict, M3253 completed the E3 measurement-A/C protocol smoke,
M3254 completed the E3 tire-truth telemetry connector smoke, M3255 completed
the full E3 measurement A/C panel, M3257 completed detector-onset
reconciliation, M3258 completed the E2' hardened clean-flip confirmation,
M3259 completed the E1' spread-revival repricing negative, and M3260
completed the E4 drift-regime pricing panel);
M3243 remains a
blocked-dependency escalation row with a resolution note because it records the
temporary roadmap stop rather than a measurement;
leak gates stopped two dataset leaks and one terminal
iteration, all per pre-registration.

PI dispositions (2026-06-12): **v5 promotion is deferred — not a live
question while research is ongoing**; v4 stays deployed, v5 remains a
filed candidate, revisit at research completion
(`docs/v5-promotion-decision-packet-2026-06.md`). **C5 next decision**:
S0-S3 rejected the original spread formulation and M3220 rejected the cheap
current-sim cg/Iz lateral rider. M3222 confirmed the C5-prime
structural-ceiling target on a fresh-seed A3 panel. **CP-1 disposition
(PI, 2026-06-12, option 1): conditional approval** — C1 opens on the frozen
C5-prime target; D1b (Chrono-native oracle pricing, searched in-backend)
added as a CP-2 precondition after the M3227 tail-replay reversal
(price-before-train rule). M3223 completed B1 moving-obstacle env engineering as a smoke-only
axis: default static obstacles and zero-relvel contracts are preserved, while
the non-default constant-velocity crosser exposes dynamic labels and ego-mode
relative velocity. M3221 found an obs-normalization/preview blocker for any
population or high-speed training; M3224 implemented the non-default B2
high-speed profile and smoke-tested it at 36 m/s, closing that env-contract
blocker for the explicit profile only. M3225 completed B3 geometry-channel
degradation and split-mu expressibility: road/active-obstacle continuous
channels can now be degraded behind an explicit config gate, while current-sim
split-mu is a documented non-expression in the `DriftObstacleEnv` single-track
outcome path. M3226 completed B4 minute-scale drive structure: raw obstacle
pass is now distinct from pass-triggered truncation, and a 60 s same-episode
warmup -> emergency obstacle -> post-pass continuation smoke passed. M3227
completed D1 Chrono S4-HF-lite direction-pricing: 108 Chrono episodes over
Sedan/BMW_E90/UAZBUS, finite reset obs72 and variant matching passed, but the
structured-oracle-tail direction was reversed in all three variants. M3228
then executed the first C1 structured-oracle demo + BC warm-start: quick smoke
passed, but the full run failed the frozen validation action-MSE gate
(0.234184 vs <=0.12). M3229 localized the failure: validation prefix MSE was
0.026446, validation tail MSE was 0.369957, and brake-channel MSE dominated
at 0.201318. M3230 then implemented the D1b Chrono-native oracle pricing
protocol smoke: the accepted rerun took 276.6 s over two row-variant pairs,
with finite obs72 resets, variant matches, and structured plus CEM native
search on both `sedan_tmeasy` and `bmw_e90_tmeasy`. Quick mode was not a
direction-pricing verdict. M3231 completed the full D1b managed panel after
an infrastructure retry: the first attempt reached 14/18 row-variant pairs
before a Chrono worker IPC deadlock, the retry dropped 1 partial row and
completed the frozen panel. Final verdict: D1b direction-positive in both
preregistered variants, with native_oracle minus same-row `v4_pertuned`
+0.2222 on Sedan (9/9 vs 7/9) and +0.1111 on BMW_E90 (8/9 vs 7/9). C1
remains open pending a revised preregistered warm-start design; C2 remains
blocked on C1, and C3 remains blocked on C2 plus PI CP-2. The D1b
direction-positive precondition for CP-2 is satisfied.
M3232 then tested the next C1 revision: the v2 preregistration added distinct
rare coast-steer train support and validation probes while keeping the M3228
MSE gate unchanged. Quick mode replayed all demos and wrote checkpoint/dataset
artifacts, but failed validation action MSE at 0.291470 (zero-action baseline
0.559903, validation rollout context 2/3 success). M3233 then synthesized the
two C1 failures with A3/D1b pricing: the C5-prime structural target remains
priced, but the local direct-MLP/action-MSE warm-start branch pivots. M3234
then priced a structured tail-family admission interface positive: direct
tail MSE 0.369957 can be represented exactly by the structured family anchor,
and the M3232 v2 preregistration has 1.0 held-out-family train coverage. C1
remains open under `c5prime_track_c_c1_tail_family_interface_smoke`; do not
run full v2, full C1 training, or C2 from the failed direct-MLP artifacts.
M3235 then passed the no-PPO tail-family interface smoke: all 11 frozen demo
replays succeeded, held-out family train coverage was 1.0, tail reconstruction
was exact over 831 tail frames, and no policy checkpoint was written. C1 now
continues under `c5prime_track_c_c1_tail_family_interface_pretrain_design`;
C2 remains blocked.
M3236 then quick-smoked the supervised pretrain path using full v2 rows plus
extra rare-tail train support. The run replayed all 43 demos and trained an
interface head, but the frozen gates failed: aggregate validation accuracy
was 0.766082, yet `structured:coast_steer_-0.7` validation accuracy was 0/101
frames and predicted-family reconstruction MSE was 0.276010 vs the <=0.1 bar.
C1 now routes to `c5prime_track_c_c1_tail_family_interface_reprice`; do not
continue local interface pretraining or controlled rollout design without
synthesis/repricing.
M3237 completed that synthesis: the C5-prime target remains priced and the
structured representation remains exact if the family is known, but local
frame-wise pretraining is closed because the aggregate validation pass hid a
complete rare-family failure. C1 now routes to
`c5prime_track_c_c1_family_selector_repricing`; no further local pretraining,
controlled rollout design, full C1 training, or C2 work is admitted before a
read-only family-selector/separability repricing milestone.
M3238 completed that repricing and rejected the local family-selector route:
no deterministic train-only selector cleared all gates. The best row-level
selector reached validation accuracy 0.803119 over the 0.538012 majority
floor, but predicted-family reconstruction MSE was 0.268415 vs <=0.1 and
`structured:coast_steer_-0.7` stayed 0/101, predicted as
`structured:brake_steer_-1.0` with negative margin. C1 local selector/interface
training is now blocked pending PI or a new nonlocal-interface pricing route;
C2/C3 remain blocked.
M3239 then moved to the next independent roadmap unit, B1b moving-obstacle
pricing, but only as a quick protocol smoke. It passed all protocol gates in
3.4 s: two moving-obstacle cells, disjoint selection/validation streams,
fixed*/inert RLS/per-cell tuned/oracle arms, and reveal-constrained oracle
attempts on every validation row. M3240 then ran the full four-cell panel and
rejected the current B1b formulation: 0/4 cells qualified, oracle-minus-
pertuned gap was 0.0000 in every cell, oracle solvability was 1.0, and
fixed_star/v4_rls/v4_pertuned all succeeded 32/32. All rows were
`aeb_feasible`, so the moving-crosser axis as priced here does not create a
type-(b) timing/prediction prize. No moving-obstacle Track C extension,
C2 admission, training, or driver-performance claim is admitted.
M3241 then moved to B2b high-speed pricing as the next independent roadmap
unit, but only as a quick protocol smoke. It passed all protocol gates in
2.0 s: two high-speed cells, disjoint selection/validation streams, raw
incumbent plus scale-aware fixed*/inert RLS/per-cell tuned/oracle arms, and
reveal-constrained oracle attempts on every validation row. M3242 then ran
the full six-cell panel and rejected the current B2b formulation by the frozen
rule: 0/6 cells qualified, oracle solvability was 1.0, oracle-minus-pertuned
gap was 0.125 in `hs24_tight_mu055` and `hs36_tight_mu075` and 0.0000 in
the other four cells, and all paired CI95 lower bounds were 0. Scale-aware
fixed_star/v4_pertuned succeeded 46/48 versus raw incumbent 42/48, so the
panel shows weak high-speed pockets and a scale-adapter transfer effect but
no priced type-(b) window-compression prize. No high-speed Track C extension,
C2 admission, training, or driver-performance claim is admitted. With B1b and
B2b closed negative, M3243 recorded the temporary roadmap stop as a blocked-
dependency escalation under
`docs/escalations/2026-06-12-phase3-roadmap-exhausted-pi-route.md`. PI then
resolved it by reopening C1 as C1-v3: residual RL on the frozen v4 reflex
base, no supervised oracle imitation, engineering-only judging. M3244 executed
the first 1024-step smoke for that route and passed all quick gates. M3245 then
executed the preregistered eight-seed stage-1 run and failed the frozen gate:
0/3 cells passed, v4+residual minus `v4_pertuned` was
-0.6276/-0.4262/-0.3299 on S1/S2/S3, and all CI95 intervals were negative. No
C2, C3, scale-up, driver-performance, high-fidelity sufficiency,
feasibility-proof, or self-ID claim is admitted by M3245. PI then opened
C1-v4 as the final distill-then-RL route. M3246 executed Stage A and passed:
the primary bounded student was within 0.05 of `v4_pertuned` in all three
cells (+0.0139/-0.0208/+0.0000), while the representation audit recorded
primary `delta_max` overbound on 17.18% of teacher frames. Stage B guarded RL
was thereby admitted with its own frozen preregistration. M3247 then ran that
Stage B first rung for 8 seeds x 1M
steps and failed the frozen rule: 0/3 pass cells, 0/3 movement cells, and
`v4_stage_b - v4_pertuned` -0.0651/-0.0425/-0.0052 on S1/S2/S3. No 4M
extension is admitted; Track C is closed unless a future proposal brings new
pricing evidence rather than another local learning-interface repair.
M3248 then opened Phase-4 Track E by completing E0: all three whitelisted
Chrono variants reset/stepped with finite obs72, and the frozen axis table
admits E1 only on selected vehicle fixtures with load-transfer physics active
while blocking independent payload-position, h_cg, tire-family, split-mu, and
continuous lf/lr/Iz/cf/cr axes without new connectors.
M3249 then passed the E1 protocol smoke across Sedan/BMW_E90/UAZBUS, writing
all four arms and structured+CEM native-oracle candidates. M3250 then ran the
full frozen E1 panel and rejected spread revival: 0/3 variants qualified,
pooled `v4_pertuned - fixed_star` was -0.0556 with CI95 [-0.1667, 0.0], and
Track F remained blocked pending the rest of Track E plus CP-3. M3251 then
passed the E2 Chrono protocol smoke: 18/18 expected quick rows, clean 9.5/30 m
reveals plus delay25 tight spot, finite reset obs and variant-match gates
true. M3252 completed the full E2 verdict on the Sedan/TMeasy fixture:
all row-count and protocol gates passed, clean oracle - best-floor qualified
at 9.5 m and 12 m, and the verdict is
`chrono_clean_belief_value_positive`. The delay25_tight readout remains
secondary. M3253 then passed the E3 A/C protocol smoke with 4/4 rows,
finite reset obs, variant matches, A long/lat detector traces, and C
baseline/v4 recovery traces. Quick mode was non-verdict. M3254 then passed
the E3 tire-truth telemetry connector smoke with 8/8 samples and 32/32 wheel
rows; every sample exposed four finite wheel rows with positive normal loads.
M3255 completed the full frozen E3 panel: 24/24 latency rows, 72/72 recovery
rows, all protocol gates passed, CP-3 evidence ready, and Track F still not
admitted. M3256 recorded the CP-3 blocked checkpoint, PI resolved it as
disposition A (harden Track E before any GPU), and M3257 completed E3-fix:
24/24 detector-onset reconciliation rows, 3426 trace rows, original early-fire
rate 0.5, reconciled early-fire rate 0.0, detector miss rate 0.1667, and E2'
dependency ready. M3258 then completed E2' hardening: 560/560 selection rows,
5760/5760 validation rows, 30 validation seeds per cell, Sedan/TMeasy plus
UAZBUS/TMeasy, all five clean reveal tiers qualified on both variants, and
the frozen clean flip criterion confirmed. Track F remains blocked on the
later PI GPU-days checkpoint. M3259 then completed E1' repricing with
selection-row oracle adequacy passed, 24 validation units per variant, 0/3
qualifying variants, pooled `v4_pertuned - fixed_star` -0.1389 CI95
[-0.2222, -0.0556], and Track F still blocked before the later PI GPU-days
checkpoint. M3260 then completed E4 drift-regime pricing: 204 rows total,
44 selection rows, 160 validation rows, all protocol gates passed, and 20
validation units per drift cell. `low_mu_power_oversteer` produced a priced
oracle headroom signal of +0.4000 vs both fixed* and tuned reflex with CI95
[0.1797, 0.6203], while `lift_off_recovery` was near-neutral at +0.0500 with
CI95 [-0.0480, 0.1480]. Reflex failures were fail-to-enter plus
fail-to-stabilize in the first cell and all fail-to-stabilize in the second.
Track F/F2 remain blocked on post-E4 PI review; M3260 makes no training,
driver-performance, high-fidelity sufficiency, paper, feasibility-proof,
repair-success, robustness-result, or self-ID claim.

## Pointer Table

| object | path |
|---|---|
| Governing thesis (two-regime law: Section 8) | `docs/capability-boundary-tracking-thesis-2026-06.md` |
| Phase-2 plan v2 (active program definition) | `docs/research-plan-phase2-capability-boundary-tracking.md` |
| Takeover decision (why M3213 was blocked) | `docs/feasibility-takeover-2026-06-route-decision.md` |
| Gate protocol v2 (anchors before informative actions; R²≤0.1 self-check) | `docs/selfid-gate-protocol-v2-2026-06.md` |
| Latest harness milestone (M3260: Phase-4 E4 drift-regime pricing) | `docs/m3260-phase4-e4-drift-regime-pricing.md` |
| Resolved blocked-dependency escalation (M3243: PI reopened C1-v3) | `docs/escalations/2026-06-12-phase3-roadmap-exhausted-pi-route.md` |
| Thesis capstone + RL re-entry (Sections 10-11) | `docs/capability-boundary-tracking-thesis-2026-06.md` |
| Data coverage map (C5 sampling design authority) | `docs/data-coverage-map-2026-06.md` |
| Incumbent deployed driver (v4, untouched) | `src/autodrift/active_safety_reflex_driver.py`, `DRIVER_ID = active_safety_reflex_driver_m3105_incumbent_v4_no_regression` |
| v5 candidate (NOT promoted; decision pending with the PI) | `src/autodrift/active_safety_driver_v5_curvature_speed_governor_candidate.py` + `docs/v5-promotion-decision-packet-2026-06.md` |
| Measurement index (script → artifact → conclusion doc) | `scripts/feasibility_audit/README.md` |

## Hard Constraints (takeover discipline)

1. **The incumbent does not move.** `ActiveSafetyReflexDriver` (v4/M3105)
   stays the deployed driver; v5 remains a candidate until the promotion
   decision packet is adjudicated by the PI, and any merged controller must
   re-run the three pre-promotion panels (recovery / fixed feasible-row /
   fresh-seed) before WP2 consumes any recoverable-set surface.
2. **Codex/autonomous execution follows the Phase-3 roadmap only.** WP6.2
   guardrails are live: validator V7 enforces feasibility-oracle-first rules,
   blocked-dependency escalation exists under `docs/escalations/`, long
   measurements use `scripts/run_managed.sh`, and task state stays explicit in
   `experiments/research_queue.csv` / `experiments/research_status.json` /
   `experiments/scoreboard.csv`.
3. **Long measurements run as managed background processes only** (the
   agent-dies-measurement-dies failure occurred 3x and is a banned pattern).
4. **Acceptance criteria are pre-registered before any run**; selection /
   validation / training seed streams are mutually disjoint and frozen in
   pre-registration JSONs.
