# Self-ID Commitment Task: Final Spec After Fix Round (2026-06-11)

## Status

- spec family: `B2K2_final` (B2 continuous-mu + K2 reveal-10 + adversarial
  repairs); authoritative data in
  `experiments/feasibility_audit/selfid_task_final_spec.json` (full
  acceptance table, 3-iteration log, panel args).
- claim boundary: task-design acceptance measurement only; no training-level,
  gate-validity, self-ID, or driver claim.
- note: the fix-round agent's run outlived its session; this document was
  written afterward from the on-disk JSON (generated 20260611T070433Z).

## Final knobs

Reveal 9.5 m; obstacle-distance jitter +/-0.75 m (floor 14.5 m); rewards
pass=40 / collision_penalty=60; mu->distance knots d=(24,38,47,52) m at
mu=(0.30,0.55,0.85,1.15); oracle speed knots v=(4.5,7.5,9.5,10.5) m/s;
deadline 5.7 s; initial speed 8 m/s on r=900 m arc; required lateral offset
2.45 m. Full table in the JSON `final_spec.env_knobs`.

## Acceptance results (validated-seed measurements)

| item | verdict | key numbers |
|---|---|---|
| P2 anti-ladder + conditional VoI | **PASS** | prior-granted (+/-0.2) conditional VoI validated = 0.3889; prior-granted ceiling cem_robust = 0.5278; tuned ladder family <= best simple fixed plan |
| P3 theta1 unavoidability depth | **PASS** | point-mass eta=1.0 deficit >= 0.5 m; in-env reactive escape 0/128 |
| P4 gate protocol inputs | **PASS** | pre-pulse single-frame mu R^2 = -0.038 (<= 0.1); post-probe single-frame R^2 = 0.9409 (anchor must precede first pulse); probe-window R^2 = 0.9999 |
| I5 integrity | **PASS** | oracle success across mu, inferability, reward tension all re-verified on final knobs |
| P1 reward alignment | **FAIL (residual)** | per-level return-vs-success gamma 0.76-0.94; tie-corrected Spearman 0.81-0.88 vs 0.9 bar (normalized-by-tie-ceiling 0.87-0.96); 40/60 rewards chosen as best of sweep |
| KE knife-edge fraction | **FAIL (residual)** | 26.8% fractional-success cells vs 15% target |

P1 and KE are recorded as residual risks: any later training pre-registration
must cite them explicitly (P1 weakens pure-return PPO signal -> staged
training with BC warm-start is mandatory, per the m1087 discipline; KE means
gate measurements need validation seed pairs throughout).

## Downstream

Gate protocol v2: `docs/selfid-gate-protocol-v2-2026-06.md` (three-signature
conjunction, gate-3 bar = 0.5278 + 0.5*0.3889 = 0.7223, anchor <= step 11,
current-frame R^2 self-check). G1' ignition gate on this spec:
`docs/selfid-g1prime-ignition-gate-2026-06.md` - verdict
FAIL_TEACHER_TASK_REWORK with a pre-registered rework route (steering-pulse
probes, demo-protocol fix, G1'' with two-sided criterion).
