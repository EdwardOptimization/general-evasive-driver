# C5' paper — adversarial review (v1) and response

The first draft was reviewed by a 5-agent adversarial pipeline (3 reviewer lenses + citation
verification + claim-vs-data audit). Findings and how each was addressed in this revision.

## Phase-5 dual-proof revision (2026-07-10)

- **Formal pre-slip theorem added.** The manuscript now defines the force-input
  differential inclusion, grip and required-slide kernels, assumptions A1-A8,
  and gives a complete inclusion proof. The direct-force abstraction and its
  steering/tire-transient realization gap are stated explicitly.
- **Weak inclusion is separated from strictness.** The theorem proves only
  `K_S subseteq K_G`. M3270 supplies the separate strict finite-boundary
  evidence: 20 frozen actions, 24 disjoint fresh-seed comparisons, 480/480
  classifications, 60/60 exact replays, and grip `D*` lower by 4.0-7.5 m in
  every comparison. The paper does not promote this into continuous Chrono
  dominance.
- **Failed continuous search retained.** M3269's missing required-slide recall
  at `mu=0.35` and one `mu=0.90` seed is reported as inconclusive rather than
  suppressed or treated as set emptiness.
- **Old post-slip claim retracted.** The earlier 9/9 countersteer-vs-brake count
  used normalized pedal zero as physical zero and mislabeled uniform braking as
  ESC. The corresponding Figure 4 and the universal ``countersteer rescues''
  claim were removed.
- **Corrected post-slip result added.** Exact control-set nesting proves weak
  recovery-set inclusion only. M3271's direct reset is rejected by tire-slip
  truth; M3272 finds 0.00 s steering advantage on four valid Chrono branches;
  M3273 finds both sets unrecoverable on 9/9 deep compact-model branches. No
  strict post-slip witness is claimed.
- **Positive control added.** The Zhao et al. 2022 unequal-yaw-rate construction
  is cited and reproduced to show that the audit detects a drift-only witness
  when the high-slip arm is deliberately granted a larger control set.

## Citation verification (IRON RULE) — all fixed
- **djeumou2024reference**: title/authors were wrong ("One Model to Drift Them All" / Goh,Topcu,
  Balachandran). Corrected to the verified arXiv:2410.20990: *Reference-Free Formula Drift with RL…*
  / Djeumou, Thompson, Suminaka, Subosits.
- **zhou2025learning**: author field malformed ("Lu, others"), title plural. Corrected to Zhou,
  Yiwen Lu, Bo Yang, Jiayun Li, Yilin Mo; "…Vehicle" (singular), per arXiv:2507.23339.
- **velenis2010analysis**: title wrong vs DOI. Corrected to the verified *Steady-State Cornering
  Equilibria and Stabilisation…* / Velenis, Frazzoli, Tsiotras, IJVAS 8:217–241 (2010).
- **Added zhao2024autonomous** (Advanced Engineering Informatics 62:102801, 2024): the
  reachability-guided emergency-drift RL line the novelty reviewer flagged as uncited — directly
  on our active-safety theme; cited in Intro/Related Work/Discussion with the delta stated.

## Statistics & methodology (rigor reviewer) — fixed
- **Drift CI tested the wrong comparator.** The headline CI is (student − floor) with floor = 0, so
  it only certified beating the reflex floor, while the load-bearing claim is beating the 0.35
  oracle. Reworded: the drift CI lower bound (0.721) exceeds the oracle; point margin 0.51.
- **Primary vs secondary CI swap.** Now report the pre-registered **paired-t** interval as primary
  (drift [0.721,0.991], avoid [-0.511,-0.089]); the cluster bootstrap is the robustness check.
- **Episode-count error.** Table 1 said "30/regime"; corrected to 20 (drift) / 30 (avoidance).
- **Post-peek re-registration disclosed.** Setup + reproducibility now state plainly that the gated
  architecture and 8→16 seed bump were chosen after the 8-seed exploratory run and the protocol
  re-frozen; the 16-seed run is confirmatory against the re-frozen protocol.
- **Five-arm vs three-column** clarified: the floor column is the max over the three learning-free
  arms.

## Domain (vehicle-dynamics reviewer) — fixed
- **Regime magnitude disclosed**: β*=0.28 rad (~16°) on μ=0.48, a single bounded drift cell, milder
  than open-loop drift demos.
- **Saddle/friction-insensitivity** attributed to Velenis (2010) alone; Goh & Gerdes (2020) cited
  for general-path drift control; the friction-blind motivation softened (motivation, not demo).
- **TMeasy fidelity caveat** added to Limitations; single-cell (not swept envelope) noted.

## Novelty/positioning (skeptical reviewer)
- **Reachability-RL line cited** (Zhao 2024) with the delta (they certify infeasibility then RL the
  manoeuvre; we pre-register the benign-regime cost).
- **"RL cannot drift" scoped** as an internal-pipeline reproducibility finding (Cai/Djeumou/Zhou/
  Sophy already drift); not a field belief.
- **Gating positioned** via Shazeer (2017) MoE; the lever-elimination diagnostic framed as the novel
  part; Cai/Sophy noted as sim-only too.

## Writing
- Reduced em-dash density; "more than 0.5" → exact "0.51".

## Deferred to a future (major) version — needs new experiments, not text
- **MPC/NMPC drift baseline arm**: acknowledged in Limitations as the stronger classical comparator;
  adding it as a 6th arm is future work (the current oracle is the best non-learning *feedback* law).
- **Per-seed validation-set frontier**: the both-good counts (8/16, 3/8) are computed on the disjoint
  **selection-eval** set (8 ep/regime), now stated explicitly in text + Fig 3 caption, because the
  committed artifact stores per-seed *combined* scores, not the per-regime validation split. A future
  run can log the per-seed validation split to put the frontier on the 30-ep validation set.
