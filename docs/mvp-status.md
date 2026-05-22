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

M149 tested that resolution surface and rejected passive input expansion as the
immediate answer. P0 + raw wheel resolved only `3.75%`; diagnostic P0 + raw
wheel + `v_parallel` resolved `12.08%`; extra-only raw/vparallel distances were
not target-aligned; longer passive P0 history resolved `23.33%` but had negative
feature-target correlation. The next frontier is hidden-cause diagnosis and
belief/active-identification targets, not adding raw wheel or diagnostic
`v_parallel` to the actor.

M150 diagnosed hidden causes on the P0-close pair surface. `future_yaw_response`
is the dominant target gap in `47.5%` of pairs. Friction is common but not
target-aligned, while mass/geometry is the strongest target-aligned hidden
group (`corr=0.409`, top-overlap `0.45`). The next frontier is therefore a
training-time capability-belief target dataset, not direct `mu` prediction.

M151 built that dataset: `240` P0-close pairs with deployable P0 student
features (`1800` dims = 25 frames x 72 features) and three teacher capability
targets for braking, yaw, and lateral response. Hidden diagnostics are included
only for training-time weighting/analysis. The next step is objective-only
sanity on this dataset before any actor or PPO integration.

M152 passed that objective-only sanity check. A deployable-history student
reduced validation combined, target, and pairwise-delta losses in `3/3`
optimization seeds on the M151 dataset. Mean validation improvements were:
combined `2.547624`, target `1.030224`, and pairwise delta `3.034799`.
This admits a guarded capability-belief hidden-state integration smoke, but it
does not yet prove closed-loop self-identification or driver behavior. PPO and
driver promotion remain blocked until behavior retention and wrong-history gates
pass.

M153 then attached the capability-belief target to the recurrent
`human_view_online_gru` response hidden state. The smoke passed in `3/3`
optimization seeds using only `25 x 72` canonical P0 history frames. Mean
validation improvements were: combined `1.751224`, target `0.655611`, and
pairwise delta `2.191227`. This proves the objective can be wired into the
current recurrent driver architecture, but still does not prove behavior. The
next required item is a behavior-retention and wrong-history gate design before
any capability-belief PPO continuation.

M154 registered that gate. It contains eight required stages: actor input
contract, behavior retention, response-history ablations, critical-key replay,
matched-history action gate, matched-history outcome gate, strict proof-surface
gate, and a promotion boundary. Passing M154 can only admit guarded PPO
continuation; it cannot promote a driver. The next step is to produce or reject
a concrete capability-belief candidate under this gate.

M155 produced the first small capability-belief auxiliary candidate from the
guarded M142 baseline. The candidate improved validation capability-belief
losses on M151 (`combined=0.548986`, `target=0.250640`,
`delta=0.596691`) and matched M142 success on the cheap seed9503 behavior
prescreen (`0.8625`). It is still rejected because the protected critical key
`9944|perturbed|28|28` failed (`0/1` accepted versus M142 `1/1`). The active
frontier remains rollout-key-safe belief learning, not PPO scale-up.

M156 repaired that failure with a smaller 20-step capability-belief update from
the same M142 baseline. The candidate keeps positive validation improvements
(`combined=0.108913`, `target=0.068497`, `delta=0.080831`), passes the
protected key (`1/1`, margin gap `0.009455`), and matches M142 success on both
cheap behavior seeds 9503 and 9504 (`0.8625`). It is admitted only to a full
M154 gate repeat; it is not yet a PPO or driver promotion.

M157 then rejects that full gate repeat at the matched-history action stage.
M156 has `0` intervention rows on the M118 action gate. Calibration shows M142
also has `0` rows under the same gate, so this is a current-baseline gate-surface
blocker rather than a M156-only regression. The next frontier is recalibrating
or remining a broad action-sensitive matched-history surface for the M142/M156
family before any PPO continuation.

M158 recalibrates that action surface and finds the concrete blocker. The M118
pairs were source-labeled `m62`, `m102`, and `m105`, so exact label matching
discarded all current `m142_a400` / `m156_s20` rows. The action gate now has a
non-default `--pair-label-mode all` for calibration, preserving
`source_checkpoint_label`. M156 clears the old M24 action thresholds after that
fix. A fresh current zero-relvel surface also shows wrong-history action signal
for M142 and M156, but per-checkpoint coverage is still below the M154 target
(`89` and `87` physical pairs versus `100`). The next frontier is M159:
broaden the current zero-relvel action surface before outcome gates or PPO.

M159 broadens that current zero-relvel surface. The top-80 cap remains negative,
but the full surface clears action-stage thresholds for both M142 and M156:
physical pairs `319` / `318`, above-threshold fractions `0.733` / `0.790`, and
closer-to-right fractions `0.719` / `0.731`. This clears only the action-stage
blocker. M156 still needs the remaining M154 matched-history outcome and strict
proof-surface gates before any PPO continuation.

M160 runs the next required M154 outcome stage and rejects PPO admission. M156's
wrong-history outcome margin gap is only `0.000284` with `3` success-drop rows;
M142 calibration is also outcome-neutral (`0.000499` margin gap, `0` success
drops). Therefore the current surface changes actions but not outcomes. The next
frontier is a current zero-relvel outcome-critical surface, not PPO.
