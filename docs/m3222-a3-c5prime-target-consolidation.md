# M3222: A3 C5-prime Target Consolidation

Status: completed. This is an auxiliary target-consolidation measurement only.
It does not admit Track C training, mutate the incumbent, apply normalization
changes, or make a driver-performance, high-fidelity sufficiency, paper,
repair-success, robustness-result, feasibility-proof, or self-ID claim. CP-1
PI approval is still required before any Track C work.

## Artifacts

- Preregistration: `experiments/feasibility_audit/c5prime_prereg.json`
- Quick smoke: `experiments/feasibility_audit/c5prime_target_consolidation_quick.json`
- Full summary: `experiments/feasibility_audit/c5prime_target_consolidation.json`
- Episode rows: `runs/feasibility_audit/c5prime_target_consolidation/episode_rows.csv`
- Managed log: `runs/managed/m3222-a3-c5prime-target-consolidation-rerun_20260611T195941Z/run.log`

## Measurement

M3222 executed roadmap A3: re-measure the C5-F1 handling-limit structural
ceiling gap on fresh seeds, using only the T-limit surface and S0-S3 target
levels.

Frozen pre-registration:

- seed base: `20260814`
- levels: `S0`, `S1`, `S2`, `S3`
- surface: `T_limit`
- instances: 12 per level
- selection rows: 6 per instance
- validation rows: 12 per instance
- primary gap: unfiltered paired `oracle_solved - v4_pertuned_success`
- target-confirmation rule: at least 3 of 4 T-limit cells must have gap
  >= 0.15 with paired bootstrap CI95 lower bound > 0

Budget: 7,776 selection episodes, 2,304 validation arm episodes, 3,725 oracle
rollouts, 48 RLS prefixes, 238.7 s CPU. The fixed global grid selected on
S0/T-limit was `(1.0, 1.45, 1.0)`.

Runtime gates passed:

- composed v4 equivalence gate
- RLS prefix construction
- selection/validation seed-disjoint sampling
- rollout semantics gate

## Result

All four target cells have oracle solvability 1.000 on the validation rows.
Three of four cells clear the pre-registered A3 target threshold. S0 is a
real positive gap with CI excluding 0, but it is below the frozen +0.15
effect-size bar and therefore does not qualify.

| cell | n | oracle | v4 pertuned | fixed star | oracle - pertuned CI95 | qualifies |
|---|---:|---:|---:|---:|---:|---|
| S0/T_limit | 144 | 1.0000 | 0.8611 | 0.8403 | +0.1389 [0.0833, 0.1944] | no |
| S1/T_limit | 144 | 1.0000 | 0.8403 | 0.8194 | +0.1597 [0.1042, 0.2222] | yes |
| S2/T_limit | 144 | 1.0000 | 0.7847 | 0.7361 | +0.2153 [0.1528, 0.2847] | yes |
| S3/T_limit | 144 | 1.0000 | 0.8264 | 0.8264 | +0.1736 [0.1181, 0.2361] | yes |

Additional fixed-star structural gaps:

| cell | oracle - fixed star CI95 |
|---|---:|
| S0/T_limit | +0.1597 [0.1042, 0.2222] |
| S1/T_limit | +0.1806 [0.1181, 0.2500] |
| S2/T_limit | +0.2639 [0.1944, 0.3403] |
| S3/T_limit | +0.1736 [0.1181, 0.2361] |

## Decision

Accept M3222 as completed A3. The C5-prime structural-ceiling target is
confirmed by the frozen rule: 3/4 T-limit cells qualify.

This does not open Track C by itself. Track C remains blocked on CP-1 PI
approval, and any population or high-speed training remains blocked by the
M3221 normalization/preview implementation issue until that is separately
resolved.

The next lowest independent OPEN roadmap item is B1 moving obstacles, unless
the PI uses CP-1 to redirect the C5-prime route first.

## Interpretation

Measured: the C5-F1 T-limit panel still contains a structural ceiling gap
above the per-instance tuned reflex floor on fresh seeds. The strongest cell
is S2/T-limit (+0.2153), and the weakest cell S0/T-limit remains positive but
below the pre-registered effect-size bar.

Inferred: C5-prime is a defensible engineering target for a future non-linear
controller study because the remaining prize is not per-instance reflex tuning
and survives a fresh-seed consolidation panel. This inference is not a
training result and not a driver-performance claim.
