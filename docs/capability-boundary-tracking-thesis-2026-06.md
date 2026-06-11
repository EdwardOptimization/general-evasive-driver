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
