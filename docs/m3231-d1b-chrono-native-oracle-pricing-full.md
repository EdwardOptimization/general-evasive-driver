# M3231: D1b Chrono-native Oracle Pricing Full

Status: completed. This is D1b high-fidelity direction pricing only. It
satisfies the CP-2 precondition "D1b direction-positive" but does not by
itself admit C3: C2 and PI CP-2 remain required. It does not mutate the
incumbent, train a policy, or make a driver-performance, validation,
promotion, high-fidelity sufficiency, paper, repair-success,
robustness-result, feasibility-proof, or self-ID claim.

## Artifacts

- Manifest: `experiments/manifests/m3231-d1b-chrono-native-oracle-pricing-full.json`
- Preregistration: `experiments/feasibility_audit/chrono_native_oracle_pricing_prereg.json`
- Full summary: `experiments/feasibility_audit/chrono_native_oracle_pricing.json`
- Candidate rows: `runs/feasibility_audit/chrono_native_oracle_pricing/candidate_rows.csv`
- Progress log: `runs/feasibility_audit/chrono_native_oracle_pricing/progress.jsonl`
- First attempt harness log: `runs/research/m3231-d1b-chrono-native-oracle-pricing-full_20260612T045005Z/command.log`
- Accepted retry harness log: `runs/research/m3231-d1b-chrono-native-oracle-pricing-full_20260612T060103Z/command.log`

## Preregistered Scope

The frozen D1b panel contains 9 A3 C5-prime current-sim structured-gap rows:
3 rows each from S1/S2/S3 at T-limit. Each row is evaluated in two Chrono
vehicle variants, `sedan_tmeasy` and `bmw_e90_tmeasy`.

The floor is the same-row A3 per-instance tuned reflex replayed on Chrono
observations. The native oracle arm keeps that reflex prefix until the
obstacle-present obs72 bit is visible, then searches Chrono-native tail
actions with 15 structured candidates and reduced-budget CEM.

## Measured

The first managed attempt reached 14/18 row-variant pairs and was
operator-terminated after the Chrono worker IPC state stopped making progress.
The accepted retry used `--resume`, dropped 1 partial baseline-only row before
continuing, and completed the remaining pairs in `492.6 s`. The final summary
contains a complete 18-pair panel and 221 CSV rows.

Protocol gates:

| gate | value |
|---|---:|
| summary written | true |
| both variants exercised | true |
| structured search exercised | true |
| CEM search exercised | true |
| reset obs finite all | true |
| variant match all | true |
| all passed | true |

Per-variant full verdict:

| variant | v4_pertuned | native_oracle | delta | candidate attempts | verdict |
|---|---:|---:|---:|---:|---|
| `sedan_tmeasy` | 7/9 | 9/9 | +0.2222 | 88 | direction_positive |
| `bmw_e90_tmeasy` | 7/9 | 8/9 | +0.1111 | 97 | direction_positive |

The BMW positive row that changed the verdict was `S2-inst08-seed7540221`:
`v4_pertuned` ended `speed_too_low`, while the native search found a CEM
candidate with `success`.

## Interpretation

D1b is positive under its frozen rule: native Chrono oracle search beats the
same-row `v4_pertuned` floor in both preregistered vehicle variants. This
rescues the structural-ceiling direction from the M3227 tail-replay proxy
reversal: the open-loop current-sim oracle tail did not transfer, but an
in-backend Chrono search still finds a positive direction.

This is still a direction-pricing result, not a high-fidelity sufficiency
claim. Absolute success rates are context only. The panel uses two Chrono
variants and does not map continuous lf/lr, Iz, cf/cr, or tire-shape hidden
parameters. The native oracle is a reduced-budget structured+CEM search, not
an all-controller proof.

## Decision

D1b is closed as completed. The CP-2 precondition "D1b direction-positive" is
satisfied. C3 remains blocked until C2 succeeds and PI CP-2 explicitly approves
the budget/staged-scale-up.
