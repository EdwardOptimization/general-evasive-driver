# M3247: C1-v4 Stage B Guarded RL

Status: completed. Frozen first-rung gate failed; no extension admitted.

## Artifacts

- Preregistration: `experiments/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl_prereg.json`
- Quick artifact: `experiments/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl_quick.json`
- Result JSON: `experiments/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl.json`
- Harness run: `runs/research/m3247-c1-v4-stage-b-guarded-rl_20260612T162234Z/command.log`
- Training metrics: `runs/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl/stage_b/training_metrics.csv`
- Candidate rows: `runs/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl/stage_b/candidate_rows.csv`
- Per-seed checkpoints: `runs/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl/stage_b/stage_b_seed_*.pt`
- Per-seed progress: `runs/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl/stage_b/progress_seed_*.json`

## Measured

M3247 executed the preregistered C1-v4 Stage B first rung through the research
harness. It initialized eight bounded residual policies from the M3246 primary
distiller, kept the M3245 `delta_max = [0.35, 0.45, 0.45]`, froze
`log_std = -1.4`, and trained each seed for 1,000,000 current-sim steps on a
new disjoint C1-v4 Stage B training stream. The incumbent
`ActiveSafetyReflexDriver` v4 was used only as the frozen base and was not
edited.

Run scale:

| metric | value |
|---|---:|
| wall time | 445.872 s |
| training seeds | 8 |
| steps per seed | 1,000,000 |
| total training steps | 8,000,000 |
| validation rows per cell | 144 |
| deterministic candidate validation episodes | 3,456 |
| pass cells | 0 / 3 |
| movement cells | 0 / 3 |

Frozen Stage B PASS required recapturing at least 50% of the A3
oracle-minus-`v4_pertuned` gap in at least two cells. A one-time 4M-step
extension was admitted only if first-rung recapture reached at least 0.15 in
at least one cell. Neither condition was met.

| cell | fixed v4 | v4_pertuned | oracle | v4_stage_b | stage_b - pertuned | CI95 | seed SE | A3 gap | recapture | pass | movement |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|---|
| S1/T_limit | 0.2014 | 0.8403 | 1.0000 | 0.7752 | -0.0651 | [-0.2813, 0.0981] | 0.1009 | 0.1597 | -0.4077 | false | false |
| S2/T_limit | 0.3194 | 0.7847 | 1.0000 | 0.7422 | -0.0425 | [-0.2352, 0.0964] | 0.0836 | 0.2153 | -0.1976 | false | false |
| S3/T_limit | 0.4861 | 0.8264 | 1.0000 | 0.8212 | -0.0052 | [-0.2222, 0.1536] | 0.0959 | 0.1736 | -0.0300 | false | false |

Seed-level gaps show the failure shape: several seeds improved over
`v4_pertuned`, but the run was not robust and one seed collapsed badly.

| seed | train success | train return mean | S1 gap | S2 gap | S3 gap |
|---:|---:|---:|---:|---:|---:|
| 20261021 | 0.9372 | 92.2578 | +0.1319 | +0.1181 | +0.1250 |
| 20261022 | 0.7950 | 81.0858 | -0.0139 | -0.0208 | +0.0903 |
| 20261023 | 0.9364 | 99.8068 | +0.1389 | +0.1111 | +0.1667 |
| 20261024 | 0.8219 | 88.4248 | -0.1181 | -0.0486 | +0.0694 |
| 20261025 | 0.4743 | 56.9205 | -0.7153 | -0.5903 | -0.6458 |
| 20261026 | 0.8618 | 87.4284 | +0.1597 | +0.1597 | +0.1667 |
| 20261027 | 0.6733 | 73.9127 | -0.1250 | -0.0556 | -0.0903 |
| 20261028 | 0.8326 | 92.0446 | +0.0208 | -0.0139 | +0.0764 |

## Inferred

C1-v4 Stage B fails the frozen first-rung rule and does not trigger the
pre-registered extension. The distilled warm start solved the M3245 discovery
problem at Stage A, but outcome RL did not robustly move beyond the
`v4_pertuned` floor toward the A3 oracle gap. The result is high variance:
four seeds are direction-positive in all or most cells, while seed 20261025
collapses enough to make the seed-averaged readout negative in every cell.

Per the C1-v4 finality clause, Track C is closed unless a future proposal brings
new pricing evidence rather than another local learning-interface repair. The
current accepted bound is: the C5-prime structural prize is real in current-sim
A3 and direction-positive under D1b Chrono-native oracle search, Stage A can
distill the `v4_pertuned` floor, but the project's tried learning interfaces
did not robustly convert that priced gap into a policy.

M3247 does not mutate the incumbent driver, does not admit C2 or C3, and does
not make a validation-ranking, driver-performance, high-fidelity sufficiency,
repair-success, robustness-result, feasibility-proof, paper, or self-ID claim.

## Next

Do not run the 4M extension: the frozen movement rule was not met. Do not open
another C1 learning attempt without new pricing evidence. The next admissible
route is paper/synthesis work that reports the priced structural gap, the
Stage-A floor distillation success, and the final Stage-B learning failure at
full fidelity.
