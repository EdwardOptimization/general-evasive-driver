# M3230: D1b Chrono-native Oracle Pricing Smoke

Status: completed. This is a D1b protocol smoke only. It does not close D1b,
satisfy CP-2, mutate the incumbent, train a policy, or make a
driver-performance, validation, promotion, high-fidelity sufficiency, paper,
repair-success, robustness-result, feasibility-proof, or self-ID claim.

## Artifacts

- Manifest: `experiments/manifests/m3230-d1b-chrono-native-oracle-pricing-smoke.json`
- Preregistration: `experiments/feasibility_audit/chrono_native_oracle_pricing_prereg.json`
- Quick summary: `experiments/feasibility_audit/chrono_native_oracle_pricing_quick.json`
- Candidate rows: `runs/feasibility_audit/chrono_native_oracle_pricing/candidate_rows_quick.csv`
- Progress log: `runs/feasibility_audit/chrono_native_oracle_pricing/progress_quick.jsonl`
- Harness log: `runs/research/m3230-d1b-chrono-native-oracle-pricing-smoke_20260612T043835Z/command.log`

## Preregistered Scope

M3230 freezes the D1b full-pricing row and vehicle selection but runs only a
minimal quick smoke:

- selected full-pricing panel: 3 current-sim structured-gap rows per S1/S2/S3
  T-limit cell, 9 rows total;
- preregistered Chrono variants: `sedan_tmeasy` and `bmw_e90_tmeasy`;
- quick smoke subset: the first selected row, `S1-inst03-seed7315000`, on
  both variants;
- native search protocol: v4 per-instance tuned reflex prefix until the
  obstacle-present obs72 bit becomes visible, then structured tail candidates
  plus reduced-budget CEM over piecewise action segments.

The full D1b direction question remains: whether the native Chrono oracle
beats the same-row `v4_pertuned` floor on the full frozen panel for each
variant.

## Measured

The accepted rerun took `276.6 s` and executed 2 row-variant pairs. The first
quick attempt is superseded because it returned after a structured candidate
success on Sedan before exercising CEM; the script was tightened and rerun
through the harness.

Quick gates:

| gate | value |
|---|---:|
| summary written | true |
| both variants exercised | true |
| structured search exercised | true |
| CEM search exercised | true |
| reset obs finite all | true |
| variant match all | true |
| all passed | true |

Per-variant quick context:

| variant | v4_pertuned | native_oracle best | structured attempts | CEM attempts | verdict |
|---|---|---|---:|---:|---|
| `sedan_tmeasy` | success | success | 5 | 4 | quick smoke, no verdict |
| `bmw_e90_tmeasy` | success | collision | 5 | 4 | quick smoke, no verdict |

## Interpretation

The D1b native-search protocol is executable in both preregistered Chrono
variants and records finite obs72 resets plus matching backend variants. The
BMW quick-row native oracle failure is not a direction-pricing result because
quick mode uses one row and a deliberately tiny search budget. It is useful as
a cost and risk signal for the full D1b run: native search may need enough
budget to avoid underpricing the oracle arm.

## Decision

M3230 admits a later D1b full managed native-oracle pricing run. D1b remains
open, C3 remains blocked on C2 plus D1b direction-positive plus CP-2, and C1
remains open pending a revised preregistered warm-start design.
