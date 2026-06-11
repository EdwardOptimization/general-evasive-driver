# Capability-Boundary Tracking: The Revised Thesis (2026-06-11)

## Status

- kind: thesis / narrative document (manual takeover session, 2026-06-11)
- scope: reformulates the project's central scientific question. Cites prior
  measurements; makes no new empirical claim beyond what the cited artifacts
  support. No driver-performance, high-fidelity, or training claim.
- provenance: distilled from the PI's three design interventions during the
  2026-06-11 feasibility takeover, each of which redirected the measurement
  program (citations inline).

## 1. Where the original formulation failed

The project's original question was **self-identification**: can a policy,
from its own command-response history, identify the hidden capability
envelope (mu, mass, actuation) and change outcomes because of it? After
~1500 milestones the outcome-level evidence was uniformly null (hidden-swap
gates ~ 0 from M28 onward; L3 never beat its own reset control across three
pilot waves; `docs/m3214-*` G1 FAIL).

The takeover's measurements located the failure precisely:

1. **The tasks never made the hidden parameters worth knowing.**
   VoI(success) = 0 on 24/24 scenario skeletons of the existing task family
   (`experiments/feasibility_audit/voi_current_task_family.json`): a single
   mu-agnostic plan reproduces the per-theta oracle success vector
   everywhere. Consistent with M67-B (a privileged teacher given mu directly
   was *worse* than the blind baseline) and M150 (mu correlates negatively
   with the future envelope target).
2. **What the gate hunted as a confound was the phenomenon itself.**
   "Current-frame substitution" - reactive adaptation from the latest
   command-response evidence - was treated for 1500 milestones as the enemy
   that gates had to rule out. The expert-driver mechanism (Section 2) shows
   it is the core of the real skill.
3. **Probe-based designs leak by construction.** A braking probe writes mu
   into the vehicle's speed - a physical register readable from a single
   frame (post-probe single-frame R^2 = 0.94-0.98,
   `docs/selfid-g1prime-ignition-gate-2026-06.md`). Any probe that changes
   persistent state defeats its own history-dependence test.

## 2. The expert-driver mechanism (PI's formulation)

Three interventions, quoted because they are load-bearing:

> "路面外观、雨刷、温度只能提供个大概范围，精确控制还是要 RL controller 来做。"
> (Side channels - road appearance, wipers, temperature - only give a coarse
> range; precise control still needs the learned controller.)

Measured consequence: conditional VoI. Coarse priors (+/-0.2 mu) hedge the
original commitment task to VoI ~ 0; tightening the reveal window (K2)
restores VoI 0.29-0.39. **Precision identification pays exactly where
reaction windows are tight** (`docs/selfid-conditional-voi-2026-06.md`,
`experiments/feasibility_audit/selfid_task_final_spec.json`).

> "真正的车手，会预估一个最大的刹车力度，慢慢加上去，身体或者手上感受到略微滑了
> 就不动了。要是加的太快或方向盘太快导致滑了，就立刻肌肉记忆救车。"
> (A real driver estimates a maximum braking force, ramps toward it
> gradually, holds the moment they feel incipient slip, and if they overshoot
> the muscle memory catches it instantly.)

This rejects the probe-then-commit paradigm outright: **identification is
embedded in the useful action itself** (threshold braking), not a separate
excitation phase. Deployability follows for free - threshold braking is
just driving; no artificial excitation protocol is needed.

> "F1 车手的循迹、漂移车手的漂移，都会避免主动到很不可控的动力学范围中。
> 都是缓慢逐渐逼近极限试探，没过极限就保持住，过了就快速纠正。"
> (F1 line-tracking and drifting alike avoid actively entering uncontrollable
> dynamics. Both gradually approach the limit, hold when not past it, and
> correct fast when past it.)

This generalizes the mechanism and supplies the missing control-theoretic
object: the boundary that matters is not the physical grip limit but the
**recoverable set** - the set of states from which the driver's own
correction law can recover.

## 3. The four-loop architecture

| driver behaviour | control structure | project artifact |
|---|---|---|
| estimate a maximum force | prior belief over the capability envelope | belief layer (to be learned) |
| ramp up gradually | confidence-scaled approach toward the limit | ramp policy family |
| feel slight slip, hold | incipient-saturation detection from command-response shortfall; boundary hold | shortfall detector (obs72-visible: commanded vs achieved ax / yaw-rate) |
| muscle-memory rescue | verified reflex recovery layer | ActiveSafetyReflexDriver v4 (deployed) / v5 candidate |

Key properties:

- **Passive fast adaptation, not active probing** ("被动快速适应，而不是主动去试").
  Excitation comes free from task actions; the expert's contribution is to
  execute useful actions in an informative way (ramp, not step), to use the
  response at high bandwidth, and to carry a prior so the next action starts
  closer to optimal.
- The shortfall signal identifies the **effective combined limit**, not mu
  itself (brake_scale and mass are also hidden) - capability
  identification, not parameter identification, echoing M150.
- F1 vs drift are the same mechanism at two operating points: riding just
  inside the physical boundary vs **stabilizing an equilibrium beyond rear
  saturation** - open-loop unstable, closed-loop stabilized by a
  high-bandwidth correction law. What licenses operating "past the limit" is
  that the state remains inside *that driver's* recoverable set.

## 4. The reformulated scientific question

Replace "does the policy maintain a hidden self-identification belief that
survives history swaps" (a *representation* question, tested by ablation)
with:

> **How fast and how precisely does the closed loop converge to and track
> the capability boundary, and what do (a) a prior and (b) correction
> bandwidth each add?** (a *rate* question, tested by regret against the
> per-theta oracle)

"Experience" decomposes into two measurable quantities:

1. **Prior quality** -> where the approach starts (time-to-boundary saved;
   in tight windows where there is no room to seek, the prior is the whole
   game - the K2/commitment regime).
2. **Correction bandwidth** -> the size of the recoverable set -> how close
   to (or how far beyond) the physical limit one dares operate.

This also retro-explains the old nulls: L2 ~ L3 because fast adaptation
needs only a short window; reset-insensitivity because the skill is a rate,
not a swappable latent; the metrics that matter are time-to-boundary,
boundary utilization ratio, overshoot depth x recovery success, and the size
of the stabilizable envelope - all absent from the success-rate-only
scoreboards.

## 5. Implications

1. **The three drift_required residual rows** (0/84 under the reflex family,
   `docs/feasibility-audit-v5-highspeed-tracking-repair-2026-06.md`) require
   sustained controlled operation beyond rear saturation - exactly the
   drift operating point. The principled path is gradual entry plus
   high-bandwidth stabilization of a beyond-saturation equilibrium, not a
   discrete "drift maneuver" command. Whether such equilibria are
   stabilizable in this simulator is a measurable question (queued).
2. **Deployable-safety principle**: constrain the learned policy's operating
   envelope to the *certified recoverable set of the verified fallback* -
   "never command a state the reflex cannot recover." The reflex layer is
   already deployed and certified at its ceiling; its recoverable set is
   being measured (`reflex_overshoot_recovery`, in flight). This is an
   empirically-certified analogue of reachability-based safety filters and
   is itself a publishable formulation.
3. **Gate design**: history-dependence tests must anchor before informative
   actions begin, and the primary readouts become rate/regret metrics
   against per-theta oracles rather than hidden-state ablations.

## 6. Measurement program in flight (wf_089e8993-3bc)

- **A. Onset detectability**: shortfall-signal detection latency vs ramp
  rate; overshoot depth = latency x rate.
- **B. Ramp-policy VoI regime map**: reveal-window sweep (9.5-30 m) x
  {per-theta oracle ramp, threshold-seeker family, prior-granted seeker,
  fixed plans} -> where the prior pays, and the speed-accuracy frontier
  ("daring to ride the edge" quantified).
- **C. Reflex recovery budget**: recoverable-set boundary of v4/v5 under
  graded overshoot (105-150% x speed x mu) - the safety budget the belief
  layer is allowed to spend.

Expected synthesis: a regime map stating where prior/belief is unnecessary
(loose windows: threshold-seeking ~ oracle), where it is decisive (tight
windows: blind commitment), and what it is worth in between (frontier
shift); then, and only then, a learnability gate for a history-bearing
policy measured in rate/regret terms.

## 7. Results addendum (2026-06-11, measurements complete)

The expectation in Section 6 was **half wrong, in the strong direction**:

- A: incipient slip is detectable from obs72 alone (140-400 ms latency at
  task-relevant ramps, zero false positives); the signal identifies the
  effective combined capability, surviving brake/mass randomization
  (`docs/selfid-threshold-seeking-onset-2026-06.md`).
- C: the v4 reflex saves 92.6% of injected overshoots; the save>=0.75
  boundary is unbroken within 150% overshoot for mu>=0.45; recovery inside
  the budget costs ~1.5-1.9 s and ~1 m. A's detection overshoots fit inside
  C's budget with 20-40 pp margin
  (`docs/selfid-reflex-recovery-budget-2026-06.md`).
- B: **VoI(belief) = 0.000 at every window tested, including the tightest.**
  The belief-free seeker matches the per-mu oracle everywhere; the
  prior-seeker is *worse* at the domain edge. The 0.39-0.44 commitment-VoI
  was real but is fully captured by embedded identification
  (`docs/selfid-threshold-seeking-regime-2026-06.md`).

Revised decomposition of "experience": detection speed and rescue bandwidth
carry all measured value; the persistent prior carries none in clean-sensing
conditions and can hurt when miscalibrated. The driver mechanism of Section
2, implemented faithfully, **dissolves the original self-ID question rather
than answering it**: there is no residual for a memory-borne belief to earn
in this simulator's task universe under noiseless observation.

The single remaining door for belief, identified by the fidelity notes and
the latency arithmetic: **observation degradation**. Detection latency is
what makes belief unnecessary; delayed/noisy ego channels lengthen it, and
the M3214 observation-degradation wrapper exists precisely to test whether
belief value re-emerges then. That is the final measurement before the
scientific story closes either way.

## 8. Final result: the two-regime law (2026-06-11, measurement complete)

The door is real. Under degraded ego-channel observation
(`docs/selfid-degraded-regime-final-2026-06.md`, 23,040 episodes,
pre-registered threshold VoI >= 0.15):

- **Belief value revives in 12/14 degraded cells** — all 7 at the tightest
  window. A mere 100 ms of self-response delay at reveal 9.5 m reopens a
  +0.208 gap; noise-and-delay cells reach 0.63-0.88.
- **Mechanism**: 0.05-sigma noise makes single-frame shortfall detection
  structurally blind (the honest threshold exceeds the largest physically
  reachable shortfall; 100% miss); detection is only redeemable by 0.5 s
  time-averaging — "noise buys delay". Embedded identification flips from
  asset to liability (detection value down to -0.417); in-task
  identification success collapses 1.00 -> 0.25-0.67.
- **Coarse priors do not substitute** (prior advantage -0.08..+0.13): what
  revives is the value of a *precise* capability belief, echoing the
  conditional-VoI finding that precision pays exactly in tight windows.
- The two clean cells bit-reproduce the Section-7 null (replication anchor).

**The two-regime law**: *where the body can sense, belief is worthless;
where sensing is delayed or drowned, belief is decisive.* Clean-sensing
passive fast adaptation is complete (the constructive null is bounded, not
universal); under realistic sensing degradation (unfiltered IMU-grade noise,
estimator/bus-chain delays — and "noisy sensor + honest filtering" lands in
the same regime as "delayed sensor") with tight reaction windows, a vehicle
that *knows its own grip envelope* retains 0.17-0.88 success where the
purely reactive identify-while-acting controller forfeits it.

This vindicates the original thesis in its precise form and finally gives
the learning program a measured prize: a history-bearing policy under
degraded observation at tight windows has 0.21-0.88 of success to capture
over the best belief-free controller — the first task condition in 3200+
milestones where that statement is backed by an oracle-level measurement.

## 9. Heterogeneous belief: vehicle vs road (2026-06-11)

The PI's third refinement — a driver also *sees what car it is* and
*drives it for a while*, building vehicle knowledge from ordinary
sub-limit feedback — decomposes the belief into two components with
opposite identifiability (`docs/selfid-belief-decomposition-2026-06.md`):

- **Sub-limit driving is structurally mu-blind**: utilization <= 0.4 leaks
  zero mu; even near-limit sub-limit driving yields only a one-sided lower
  bound. The same gentle data identifies the vehicle authority ratios to
  < 1% — vehicle and road knowledge come through orthogonal channels.
- **The prize is road knowledge.** Across all degraded cells the road
  component ~ equals the whole matched prize; the vehicle component is
  <= 0.19, exists only in light-degradation cells, and the interaction is
  negative and equal: the two are **substitutes**. Vehicle knowledge is
  instrumental — vehicle uncertainty alone lifts the shortfall-detection
  floor from 0.08 to 0.29, so knowing the car repairs the grip detector;
  once mu is known it adds ~nothing.
- **Familiarization is cheap and bounded**: 5 s of ordinary driving
  recovers the entire vehicle share (kappa error 0.0025); under sensor
  noise a naive estimator hits an errors-in-variables bias floor that
  time-averaging does not remove (an IV fix via the undegraded command
  channels is the engineering answer).
- **Ladder update**: the hierarchy becomes two-dimensional — temporal
  integration depth (L0-L3) x information source. "Driving it for a
  while" is L3.5 (drive-scale slow proprioceptive belief); "seeing the
  car type" is L4 (exogenous categorical prior). Measured: both are
  capped by the vehicle share, L3.5 saturates the cap in 5 s, so L4 can
  at most shorten the familiarization — and is worth zero where sensing
  noise erases the vehicle component entirely. The expert's edge,
  re-confirmed: knowing the car is how you *feel the road better*; the
  road is what decides.

## 10. Capstone: belief writes itself into the state (2026-06-11)

The WP1 program (M3216/M3217) ended on a terminal bound whose mechanism
recurred four times across the arc, each time at a deeper level:

1. a braking probe writes mu into the *speed register* (G1');
2. mu-correlated arrival timing writes into the *geometry channels*
   (M3216 leak 1);
3. convergence transients write into the *longitudinal channels*
   (M3216 leak 2);
4. a competent closed-loop seeker's approach state at the decision tick
   encodes *its own belief* — so on-policy training data matched to the
   evaluation distribution is necessarily single-frame readable, mutually
   exclusive with the attribution gate (M3217 terminal stop).

The converging statement: **in a deterministic, fully-actuated system,
any belief that influences action becomes current-frame readable; the
more competent the agent, the more its state encodes its knowledge.**
Current-frame substitution — treated for 1500 milestones as an
experimental nuisance — is a property of competent embodied behavior.
This is the deepest available explanation of the original nulls, and it
fixes the final scope of the program's claims: capability belief is
learnable from degraded history (M3216 estimator, R^2 0.91-0.99,
history-borne by reset control), its value is real and measured at the
oracle level (the mode-dependent two-regime law), but *behavioral*
attribution of that value to history is structurally self-erasing in
closed loop — the knowledge migrates into the state it produces. The
honest deliverables are exactly these three measured statements plus
their boundary.

## 11. The capstone's constructive reading: RL re-enters as engineering
(PI directive, 2026-06-11)

> "RL 的优势是，把对车辆和极限情况的辨识都放在网络中，有非常强的
> 自适应性（在机器人领域被大量证明过），而且直接控制油门、刹车、转向，
> 能做出非线性情况下的动作。就算是同一款车，重量不同、季节不同、
> 有无改装，车辆动态会差很多——不可能一个一个去调反射控制器。"

The capstone cuts both ways. It closes the *scientific* question
(history attribution is self-erasing) and simultaneously reopens the
*engineering* one: if competent closed-loop behavior necessarily encodes
its knowledge in state, then implicit adaptation — RL's native mode —
is the natural carrier of capability belief, and demanding modular
attribution was the wrong interface all along (WP1's substitution
failure and M3217's gate stop are the measured form of this). RL died
twice in this project as an evidence source (m1087 washout; G1 variance
floor) and returns with a clean position: an engineering executor,
judged purely on outcomes against measured floors and per-instance
oracles. The first population-spread pricing pass then split the user's
original C5 argument in two. The mass/brake/tau spread mechanism did
**not** price out in S0-S3, but the reflex structural-ceiling gap did:
+0.16-0.21 at T-limit, CI-excluding 0, concentrated in drift-grade rows.
M3220 then ran the cheap current-sim lateral rider over cg/Iz and also
found no spread prize: 0/4 cells qualified, with S4L/T-limit at only
+0.007 CI95 [-0.014, +0.028]. M3222 then re-measured the surviving C5'
target on fresh C5-F1 T-limit seeds and confirmed it by the frozen A3 rule:
3/4 cells qualified, with S1/S2/S3 oracle-minus-pertuned gaps
+0.1597/+0.2153/+0.1736 and CI95 lower bounds > 0; S0 remained positive but
below the +0.15 effect-size bar (+0.1389). The remaining population question
is now narrower and higher-fidelity: whether tire-shape, load-transfer,
wheelbase-class, or Chrono vehicle-family dynamics move the boundary. M3218
found Chrono resources for that extension but also found the repo wiring still
hard-coded to Sedan + TMeasy; M3219 then added and smoked the reset-time
selector on default Sedan, BMW_E90, and UAZBUS. S4 pricing now waits on a
frozen preregistration, not on backend wiring. Claim C5 and the WP-RL program
operationalize this discipline: price first, then train RL only against a
measured, pre-registered gap after CP-1.
