# M2041 Paper-Route Controlled Routing Smoke Branch Synthesis

- status: completed
- decision: `controlled_routing_smoke_synthesis_pivot_to_no_rerun_outcome_localization`
- synthesis decision: `pivot`
- manifest: `experiments/manifests/m2041-paper-route-controlled-routing-smoke-branch-synthesis.json`
- evidence window: M2031-M2040
- reset/rollout/measured execution in M2041: `false`
- policy actions executed in M2041: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2031-M2040 advanced the controlled routing-smoke route from command design to
complete measured execution:

```text
M2031: existing runners rejected as lossy for the M2029 generated-source
       provenance; materialization adapter required.
M2032: 36-source x 12-profile no-reset materialization adapter designed.
M2033: materialization pass, 36 selected sources, 36 executable specs,
       432 workload rows, guardrail 0, generated rows marked smoke_proxy.
M2034: materialization audit admits reset-only validation.
M2035: focused reset validator designed because older validators would drop
       M2033 metadata.
M2036: reset-only validation pass, 36/36 reset success, observation dimension
       failures 0, metadata missing 0, contract violations 0, guardrail 0.
M2037: reset audit admits measured execution command design.
M2038: focused measured runner designed because older measured runners were
       hard-coded or schema-incompatible.
M2039: measured execution pass, 432/432 episodes, failure 0, metric
       completeness failures 0, guardrail 0.
M2040: result audit rejects direct ranking due sparse successes and broad
       offtrack dominance.
```

The key M2039 outcome snapshot is:

```text
success_obstacle_pass: 20 / 432
collision_failure: 13 / 432
off_track_noncollision_noncompletion: 399 / 432
success_rate: 0.046296
collision_rate: 0.030093
clearance_margin_mean: 10.530665
```

Profile-level support is sparse:

```text
L3_online_gru: 8 / 36 success
L3_reset_control_corrected: 8 / 36 success
L1_one_step: 4 / 36 success
all L2 finite-window profiles: 0 / 36 success each
L0_current_masked: 0 / 36 success
```

## Supported Claims

Supported:

```text
The routing-smoke materialization/reset/measured-execution pipeline now works
for the selected 36-source, 12-profile, 432-cell smoke panel.

M2033/M2036/M2039 preserved the registered provenance and guardrail boundaries.

M2039 produced real measured rollout data, not just schema or reset evidence.

M2040 correctly blocks direct ranking because outcomes are low-support and
offtrack-dominated.
```

## Falsified Claims

Falsified or unsupported:

```text
The 432-cell routing smoke is ready for controller-family ranking.

The current panel can support a finite-window-vs-GRU conclusion.

The generated T2/T3 rows are paper-valid benchmark tasks rather than smoke
proxies.

The measured execution supports level3 self-identification.

The next step should be another runner/adapter repair before understanding
where the 20 successes and 399 offtrack outcomes come from.
```

## Failure Taxonomy Summary

Primary failure types:

```text
outcome_support_low
behavior_regression
```

Interpretation:

- This is not a materialization, reset, runner, metric-completeness, or
  guardrail failure.
- The active blocker is evidence quality: the measured execution is complete,
  but most rows end off-track before a fair controller-family comparison can be
  claimed.
- The high offtrack count may indicate task-quality issues, profile/task
  mismatch, generated-proxy hardness, or slices where some controllers are not
  meaningful. That must be localized before repair or ranking.

## Public Gate Overfit Risk

Risk:

```text
medium-to-high if the project keeps tuning the same smoke panel or profiles
without first localizing the outcome distribution.
```

Reasons:

- The M2039 success count is small enough that ranking could be dominated by a
  handful of source rows.
- The generated T2/T3 rows are smoke proxies and should not silently become
  paper-level benchmark evidence.
- Offtrack dominance can hide whether failures are due to controller capability,
  scenario quality, termination geometry, or profile/task mismatch.
- A direct finite-window-vs-GRU comparison would overfit to the current
  offtrack-heavy panel.

## Next Branch Decision

Decision:

```text
pivot_to_paper_route_controlled_routing_smoke_outcome_localization
```

M2042 should implement and run a no-rerun outcome localizer over M2039
artifacts. It should reproduce the M2039 counts exactly and localize outcomes
by:

```text
profile;
task family;
source_kind;
proxy_template;
generated_proxy / original source;
profile x family;
profile x source_kind;
profile x generated_proxy.
```

The localizer should decide whether any bounded diagnostic slice is
comparison-worthy or whether the next route should be task-quality repair.

Rejected now:

```text
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark table;
new rollout before localizing existing outcomes;
another narrow runner/adapter milestone.
```

Controller ranking, paper-level comparison, high-fidelity validation,
finite-window-vs-GRU conclusions, and level3 self-ID claims remain blocked.
