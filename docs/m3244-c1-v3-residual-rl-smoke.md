# M3244: C1-v3 Residual-RL Smoke

Status: completed. This is an engineering smoke only.

## Artifacts

- Preregistration: `experiments/feasibility_audit/c5prime_c1_v3_residual_rl_smoke_prereg.json`
- Result JSON: `experiments/feasibility_audit/c5prime_c1_v3_residual_rl_smoke.json`
- Harness run: `runs/research/m3244-c1-v3-residual-rl-smoke_20260612T131835Z/command.log`
- Checkpoint: `runs/feasibility_audit/c5prime_c1_v3_residual_rl_smoke/quick/checkpoint.pt`
- Metrics: `runs/feasibility_audit/c5prime_c1_v3_residual_rl_smoke/quick/metrics.csv`
- Episode rows: `runs/feasibility_audit/c5prime_c1_v3_residual_rl_smoke/quick/episode_rows.csv`
- Rollout arrays: `runs/feasibility_audit/c5prime_c1_v3_residual_rl_smoke/quick/rollout_arrays.npz`

## Measured

M3244 executed the PI-reopened C1-v3 route at smoke scale: a small MLP PPO
policy emitted bounded residual actions on top of the frozen
`ActiveSafetyReflexDriver` v4 base. The action rule was:

`action = clip(v4(obs) + delta_max * residual(obs), -1, 1)`

with `delta_max = [0.35, 0.45, 0.45]`. The smoke used reward recalibration
`pass_reward=40`, `collision_penalty=60`, and selected two structural-gap A3
rows from each qualified C5-prime level S1/S2/S3.

All preregistered quick gates passed:

| gate | value |
|---|---|
| total steps exactly 1024 | true |
| S1/S2/S3 exercised | true |
| finite observations/actions/rewards/advantages/losses | true |
| final actions in bounds | true |
| residual deltas bounded | true |
| optimizer changed parameters | true |
| checkpoint written | true |
| metrics written | true |

Run metrics:

| metric | value |
|---|---:|
| environment steps | 1024 |
| completed episodes | 10 |
| levels seen | S1, S2, S3 |
| mean step reward | 0.476609 |
| mean episode return | 48.281069 |
| initial loss | 100.505173 |
| final loss | 102.000290 |
| parameter delta L2 | 0.185837 |
| script wall time | 1.285 s |

Rows exercised:

| row | level | v4 pertuned outcome | oracle family |
|---|---|---|---|
| S1-inst00-seed7300078 | S1 | collision | structured:brake_steer_-0.4 |
| S1-inst01-seed7305013 | S1 | collision | structured:full_brake |
| S2-inst00-seed7500026 | S2 | collision | structured:brake_steer_-0.4 |
| S2-inst00-seed7500156 | S2 | collision | structured:full_brake |
| S3-inst00-seed7700182 | S3 | collision | structured:brake_steer_-0.4 |
| S3-inst01-seed7705078 | S3 | collision | structured:brake_steer_-0.4 |

## Inferred

The C1-v3 residual route is now technically runnable through the real C5-prime
current-sim environment, with frozen v4 base actions, bounded residual deltas,
and an optimizer update that reaches disk-backed artifacts. This clears only
the 1024-step smoke prerequisite for designing a separate stage-1 run.

M3244 does not admit C2 or C3. It does not measure residual performance against
`v4_pertuned`, does not execute the four-arm judging protocol, and does not
make a driver-performance, high-fidelity sufficiency, repair-success,
feasibility-proof, paper, or self-ID claim.

## Next

The next admissible C1-v3 unit is a stage-1 preregistration: fixed v4 /
`v4_pertuned` / v4+residual / oracle readouts on frozen validation seeds,
seed-clustered uncertainty, and the frozen PASS rule of recapturing at least
50 percent of the A3 gap in at least two of the three qualified T-limit cells.
CP-2 remains budget-only because the D1b direction-positive precondition was
met by M3231; PI approval is still required before any run over one hour.
