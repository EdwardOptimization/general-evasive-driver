# M3245: C1-v3 Residual-RL Stage-1

Status: completed. Frozen stage-1 gate failed.

## Artifacts

- Preregistration: `experiments/feasibility_audit/c5prime_c1_v3_residual_rl_stage1_prereg.json`
- Quick artifact: `experiments/feasibility_audit/c5prime_c1_v3_residual_rl_stage1_quick.json`
- Result JSON: `experiments/feasibility_audit/c5prime_c1_v3_residual_rl_stage1.json`
- Harness run: `runs/research/m3245-c1-v3-residual-rl-stage1_20260612T134531Z/command.log`
- Training metrics: `runs/feasibility_audit/c5prime_c1_v3_residual_rl_stage1/stage1/training_metrics.csv`
- Candidate rows: `runs/feasibility_audit/c5prime_c1_v3_residual_rl_stage1/stage1/candidate_rows.csv`
- Checkpoints: `runs/feasibility_audit/c5prime_c1_v3_residual_rl_stage1/stage1/checkpoints.pt`
- Progress: `runs/feasibility_audit/c5prime_c1_v3_residual_rl_stage1/stage1/progress.json`

## Measured

M3245 executed the preregistered C1-v3 stage-1 protocol through the research
harness. It trained eight bounded MLP residual policies over the frozen
`ActiveSafetyReflexDriver` v4 base, with `delta_max = [0.35, 0.45, 0.45]`,
reward `pass_reward=40`, and collision penalty `60`. Training used disjoint
C5-prime T-limit rows generated from the new `20260911` seed stream; validation
used the frozen A3 S1/S2/S3 T-limit rows.

Run scale:

| metric | value |
|---|---:|
| wall time | 140.333 s |
| training seeds | 8 |
| steps per training seed | 8192 |
| total training steps | 65536 |
| training episodes completed | 683 |
| validation rows per cell | 144 |
| deterministic candidate validation episodes | 3456 |
| stage-1 pass cells | 0 / 3 |

The frozen decision rule was not met: PASS required recapturing at least 50
percent of the A3 oracle-minus-`v4_pertuned` gap in at least two of the three
qualified T-limit cells.

| cell | fixed v4 | v4_pertuned | oracle | v4+residual | residual - pertuned | CI95 | seed SE | A3 gap | recapture | pass |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|
| S1/T_limit | 0.2014 | 0.8403 | 1.0000 | 0.2127 | -0.6276 | [-0.7058, -0.5460] | 0.0032 | 0.1597 | -3.9299 | false |
| S2/T_limit | 0.3194 | 0.7847 | 1.0000 | 0.3585 | -0.4262 | [-0.5087, -0.3394] | 0.0133 | 0.2153 | -1.9796 | false |
| S3/T_limit | 0.4861 | 0.8264 | 1.0000 | 0.4965 | -0.3299 | [-0.4132, -0.2439] | 0.0180 | 0.1736 | -1.9001 | false |

Training did update the residual policies: parameter L2 deltas ranged from
1.1026 to 1.2243 across the eight seeds. Mean training episode return ranged
from 38.0831 to 47.2216, so the run was not a no-op wiring failure. The
deterministic validation policy nevertheless stayed near raw fixed v4 and far
below the `v4_pertuned` floor:

| cell | candidate successes | candidate episodes |
|---|---:|---:|
| S1/T_limit | 245 | 1152 |
| S2/T_limit | 413 | 1152 |
| S3/T_limit | 572 | 1152 |

## Inferred

C1-v3 stage-1 fails the frozen gate. At this budget and with this residual
architecture, direct PPO on a bounded residual over fixed v4 did not recover
any of the A3 structural-ceiling prize; it underperformed the honest
`v4_pertuned` floor in every qualified cell, with paired CIs entirely on the
negative side.

This is a behavior result, not an infrastructure failure. The residual wrapper,
training loop, multi-seed evaluation, and four-arm readout all executed and
wrote artifacts. The result does not prove that no residual-RL approach can ever
work, but it does reject this preregistered stage-1 attempt and does not admit
scale-up.

M3245 does not mutate the incumbent driver, does not admit C2 or C3, and does
not make a validation-ranking, driver-performance, high-fidelity sufficiency,
repair-success, robustness-result, feasibility-proof, paper, or self-ID claim.

## Next

Do not proceed to C1-v3 scale-up or any run over one hour from this result.
The next admissible action is synthesis or PI route selection: either accept the
negative stage-1 result as closing this residual-on-v4 attempt, or preregister a
new priced route with a different mechanism. Criteria should not be loosened
against M3245.
