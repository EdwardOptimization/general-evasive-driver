# M3264 Phase-4 F2 Asymmetric Actor-Critic RL

## Status

- Verdict: f2_completed (full run: 8 training seeds, 30 validation episodes/regime, training-seed-clustered CIs; engineering-only, incumbent unchanged, defers to PI review).
- Scope (S3): real asymmetric actor-critic RL (PPO + bootstrapped privileged GAE critic + policy gradient); teacher = BC warm-start / annealed auxiliary only.
- Engineering-only; incumbent unchanged; no self-ID claim.

## Four-arm success (validation, disjoint seeds, all training seeds B3)

| regime | fixed_star | entry_speed_commitment_floor | online_mu_seeker_floor | per_regime_oracle | student_policy |
|---|---:|---:|---:|---:|---:|
| avoidance | 1.000 | 1.000 | 1.000 | 1.000 | 0.700 |
| drift | 0.000 | 0.000 | 0.000 | 0.350 | 0.856 |
| pooled | 0.600 | 0.600 | 0.600 | 0.740 | 0.762 |

## Prize recovery + cross-training-seed CI (B4; full validation, training-seed-clustered CIs)

- drift student-minus-floor: 0.856; paired-t CI {'n': 16, 'mean': 0.85625, 'ci95_low': 0.721167, 'ci95_high': 0.991333, 'sd': 0.253558, 't_crit': 2.131, 'method': 'paired_t'}
- avoidance student-minus-floor: -0.300; paired-t CI {'n': 16, 'mean': -0.3, 'ci95_low': -0.511018, 'ci95_high': -0.088982, 'sd': 0.396092, 't_crit': 2.131, 'method': 'paired_t'}
- student avoidance no-regression: False
- reward alignment (B6, per-episode rank-biserial AUC hard gate; Spearman reported): {'spearman': 0.977683818093033, 'auc': 0.9997607583958851, 'per_regime': {'avoidance': {'auc': 1.0, 'spearman': 0.977683818093033, 'n': 600, 'applicable': True, 'meets_0p9': True}, 'drift': {'auc': 0.9997607583958851, 'spearman': 0.7917315633386083, 'n': 400, 'applicable': True, 'meets_0p9': True}}, 'n_episodes': 1000, 'meets_0p9': True, 'gate_statistic': 'rank_biserial_auc', 'tie_degenerate': False, 'gate_applicable': True}
- S7 oracle ceiling precheck: {'avoidance': 1.0, 'drift': 0.35} -> proceed

## Artifacts

- Preregistration (FREEZE-READY draft): `experiments/feasibility_audit/phase4_f2_prereg.json`
- Full JSON: `experiments/feasibility_audit/phase4_f2.json`
- Arm rows: `runs/feasibility_audit/phase4_f2/arm_rows_full.csv`
- Checkpoints: `runs/feasibility_audit/phase4_f2/checkpoints_full`

## Claim Boundary

Phase-4 F2 asymmetric actor-critic RL training and four-arm adjudication: asymmetric actor(obs72)/critic(obs72+privileged) Gaussian policy trained by PPO (clipped surrogate + bootstrapped privileged GAE critic + entropy) from the recalibrated reward, with the avoidance entry-speed oracle and drift DriftFeedbackPolicy as BC warm-start/annealed-auxiliary teachers only, held-out task-score selection on a disjoint eval set, a mu/reveal avoidance spectrum, and a frozen {fixed*/entry-speed-floor/online-mu-seeker/per-regime-oracle/student} four-arm validation comparison with training-seed-clustered CIs. The FULL run IS a conditional driver-performance result on the F2 validation distribution -- it is engineering-only: it does not mutate ActiveSafetyReflexDriver, makes no self-ID or history-attribution claim, and is NOT a promotion, incumbent change, current-sim sufficiency, full high-fidelity sufficiency, paper, repair-success, or feasibility-proof claim.
