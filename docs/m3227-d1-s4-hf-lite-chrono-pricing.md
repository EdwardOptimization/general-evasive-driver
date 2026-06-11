# M3227: D1 S4-HF-Lite Chrono Pricing

Status: completed. This is a high-fidelity direction-pricing measurement only.
It does not run training, mutate a driver, admit Track C, or make a validation
ranking, promotion, driver-performance, high-fidelity sufficiency, paper,
repair-success, robustness-result, feasibility-proof, or self-ID claim.

## Artifacts

- Preregistration:
  `experiments/feasibility_audit/s4_hf_lite_chrono_pricing_prereg.json`
- Quick smoke:
  `experiments/feasibility_audit/s4_hf_lite_chrono_pricing_quick.json`
- Full summary:
  `experiments/feasibility_audit/s4_hf_lite_chrono_pricing.json`
- Episode rows:
  `runs/feasibility_audit/s4_hf_lite_chrono_pricing/episode_rows.csv`
- Progress log:
  `runs/feasibility_audit/s4_hf_lite_chrono_pricing/progress.jsonl`
- Harness command log:
  `runs/research/m3227-d1-s4-hf-lite-chrono-pricing_20260611T212929Z/command.log`
- Script:
  `scripts/feasibility_audit/s4_hf_lite_chrono_pricing.py`

## Method

M3227 froze 12 A3 C5-prime rows before the full Chrono rollout: four rows each
from S1/S2/S3 T-limit. Every selected row was a current-sim structured-gap row:
`v4_pertuned` failed, the A3 oracle solved it, and `oracle_by` was a
reproducible `structured:*` action family. CEM-solved rows were excluded because
A3 did not persist CEM action sequences.

The three Chrono variants were:

- `sedan_tmeasy`
- `bmw_e90_tmeasy`
- `uazbus_tmeasy`

The three arms were:

- `fixed_star`: A3 pooled S0/T-limit fixed grid reflex.
- `v4_pertuned`: A3 per-instance tuned grid reflex.
- `structured_oracle_tail`: A3 structured oracle action replay, using the
  `fixed_star` prefix until the obstacle-present obs72 bit becomes visible in
  the Chrono rollout.

Continuous `lf/lr/cg_shift`, `Iz/inertia_scale`, and `cf/cr/tire_curve_family`
are still not mapped into Chrono. D1 treats vehicle selection only as a
discrete geometry/inertia/tire-fixture bracket; backend reset metadata was
recorded for every episode. Scenario mass, brake/drive force scales, and
control-layer lags remain the frozen A3 row values.

## Measured

The full rollout ran 108 Chrono episodes in 1244.6 s. Reset obs72 was finite
and requested variant matching passed for all rows.

| Chrono variant | fixed_star success | v4_pertuned success | structured_oracle_tail success | oracle - pertuned | verdict |
|---|---:|---:|---:|---:|---|
| `sedan_tmeasy` | 7/12 | 6/12 | 5/12 | -0.0833 | reversed |
| `bmw_e90_tmeasy` | 6/12 | 3/12 | 2/12 | -0.0833 | reversed |
| `uazbus_tmeasy` | 7/12 | 8/12 | 2/12 | -0.5000 | reversed |

Failure modes:

| Chrono variant | fixed_star failures | v4_pertuned failures | structured_oracle_tail failures |
|---|---|---|---|
| `sedan_tmeasy` | collision 5 | collision 6 | collision 6, offtrack 1 |
| `bmw_e90_tmeasy` | collision 5, speed_too_low 1 | collision 4, offtrack 3, speed_too_low 2 | collision 5, offtrack 2, speed_too_low 3 |
| `uazbus_tmeasy` | collision 5 | collision 4 | collision 8, offtrack 2 |

The quick smoke was not the primary verdict. It ran 27 episodes and already
showed mixed direction (`sedan_tmeasy` neutral, `bmw_e90_tmeasy` preserved,
`uazbus_tmeasy` reversed), which motivated completing the frozen full panel.

## Inferred

Under the preregistered D1 proxy, the A3 current-sim structural-gap direction
does **not** preserve across Chrono multi-vehicle variants. The direct replay
of current-sim structured oracle tails is worse than the per-instance tuned
reflex floor on all three Chrono vehicles.

This is a negative D1 result, not a refutation of the A3 current-sim result.
M3227 did not run a fresh high-fidelity oracle search, did not map continuous
lateral/tire channels, and did not price a learned nonlinear policy. It only
tests whether the already-selected current-sim structured tails transfer as
fixed action families through the existing Chrono variant selector.

## Decision

D1 is complete with a negative/reversed direction-preservation verdict:
all three requested Chrono vehicles are `reversed` by the frozen rule.

Any future Chrono-side structural-prize claim would need a new preregistered
pricing route, likely with a high-fidelity oracle search and an explicit
decision about whether to map or continue bracketing the missing
`lf/lr/Iz/cf/cr` channels. Track C remains blocked on CP-1.
