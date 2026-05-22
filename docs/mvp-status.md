# AutoDrift MVP Status

Last updated: 2026-05-20

## Objective

Build a reproducible AutoDrift engineering MVP that studies RL control for
AEB-infeasible AES/drift-avoidance scenarios under nonlinear tire and drift
dynamics. Each stage needs tests, benchmarks, documentation, and clear
conclusions, including negative results.

## Completion Checklist

| Requirement | Evidence | Status |
| --- | --- | --- |
| Reproducible infrastructure | `docs/setup.md`, `docs/infrastructure.md`, `pyproject.toml`, `configs/`, `runs/` manifests | complete |
| Literature and project framing | `docs/related-papers.md`, `docs/drifting-rl-nmpc-reading-notes.md`, `docs/emergency-drift-avoidance-related-work.md` | complete for MVP |
| RL circular drift baseline | `docs/m2-circular-drift-results.md`, `runs/benchmark_ppo_circle_m2_seed113_recover2_200eval` | complete |
| Friction adaptation | `docs/m3-friction-adaptation-plan.md`, `runs/benchmark_ppo_m3_staged_history_seed47_init_m2_100eval` | first pass complete |
| Variable-curvature tracking | `docs/m4-general-path-tracking.md`, `runs/benchmark_ppo_m4_figure_eight_survival_seed71_segment_100eval` | diagnosed, not fully solved |
| AEB-infeasible obstacle scenarios | `src/autodrift/scenarios.py`, `configs/m5_obstacle_*.json`, `docs/m5-emergency-avoidance.md` | complete for MVP |
| AEB/AES/drift-required buckets | `obstacle_label_summary.csv` in M5 benchmark runs | complete |
| RL obstacle avoidance | `runs/benchmark_ppo_m5_obstacle_seed83_avoidable_100eval`, `runs/benchmark_ppo_m5_obstacle_seed83_drift_required_100eval` | first pass complete |
| Baselines | `aeb`, `aes_heuristic`, `envelope_aes`, `docs/m6-model-based-baselines.md` | first pass complete |
| Tests | `pytest` | complete |
| Clean commit history | `git log` contains staged M2-M6 commits, current worktree clean after final commit | complete |

## Key Results

M2 circular drift:

- checkpoint success: `1.000` over 200 seeds;
- heuristic success: `0.165`.

M3 friction-step adaptation:

- M2 static checkpoint on friction-step task: `0.770` success;
- M3 initialized history checkpoint: `0.810` success.

M4 figure-eight tracking:

- best RL checkpoint: `0.830` success;
- heuristic: `1.000` success;
- conclusion: M4 remains a low-friction tracking weakness, with segment
  diagnostics showing friction as the primary blocker across left and right
  curves.

M5 AEB-infeasible avoidance:

- avoidable benchmark RL success: `0.860`;
- drift-required benchmark RL success: `0.860`;
- AEB baseline drift-required success: `0.050`;
- heuristic AES drift-required success: `0.500`;
- friction-envelope AES drift-required success: `0.790`.

## MVP Conclusion

The MVP is complete as a reproducible simulation and benchmark platform:

- it can generate AEB-infeasible obstacle scenarios;
- it separates `aes_feasible`, `drift_required`, and `unavoidable` buckets;
- it trains and evaluates RL policies against fixed-seed baselines;
- it demonstrates RL outperforming AEB-only, heuristic AES, and a stronger
  friction-envelope AES baseline on `drift_required` scenarios.

The MVP is not a sim-to-real or safety-certified controller. Remaining research
work includes broader obstacle geometry, stronger balanced sampling, more
robust low-friction figure-eight tracking, and a true NMPC baseline once the
scenario surface stabilizes.

## Current Research Frontier

As of 2026-05-22, the active research frontier is no longer MVP viability. The
project is testing whether a deployable recurrent policy can use its own
history of commands and vehicle response for online capability-envelope
self-identification.

Recent input audits:

```text
M143: supervised driver-like profile audit
M144: learned-history repeat
M145: speed-cue audit
M146: body-feedback observability audit
```

M146 artifacts:

```text
runs/m146_body_feedback_seed9480/summary.json
runs/m146_body_feedback_seed9481/summary.json
runs/m146_body_feedback_seed9482/summary.json
runs/m146_body_feedback_multiseed/summary.json
docs/m146-body-feedback-observability-audit.md
```

Key M146 aggregate results:

| Delta | Post-slip AUC delta | Pre-limit R2 delta |
| --- | ---: | ---: |
| passenger body+scene - body only | 0.166508 | 0.014227 |
| H1 - passenger body+scene | -0.027005 | -0.044467 |
| P0 - H1 | 0.014683 | 0.004110 |

M146 found `434` ambiguous H1 body-history candidate pairs across three seeds,
with `150` rows exported. Decision: keep P0 as the current human-view input
contract and do not restart PPO from a new narrower H1 profile.

M147 then checked whether those exported H1-ambiguous pairs are resolved by
existing candidate signals. Full P0 resolved only `15.3%`, raw wheel `18.7%`,
and diagnostic raw wheel + `v_parallel` `30.7%`. Extra-only channels separate
many pairs, but their distance is weakly target-aligned. The next input question
is therefore stricter: mine pairs that remain close under current P0, not only
under narrowed H1.

M148 answered that stricter question positively: P0-close target-divergent pairs
remain numerous. Across three seeds it found `346` P0-close target-divergent
pairs over `108` episode-pairs, with a P0/H1 ambiguity-count ratio of
`0.922667`. Current P0 may therefore be information-limited for future-envelope
self-identification; the next step is to test target-aligned resolution of those
P0-close pairs.
