# M2146 Paper-Route Outcome-Supported Decisive Comparison-Support Post-Diagnostic Synthesis

- status: completed
- decision: `comparison_support_post_diagnostic_synthesis_pivot_to_current_sim_controlled_comparison_benchmark_design`
- synthesis_decision: `pivot`
- synthesis window: `M2136-M2145`
- reset/rollout/measured execution in M2146: `false`
- policy actions executed in M2146: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2136-M2145 completed the post-M2135 diagnostic loop over the
comparison-support generated-proxy branch:

```text
M2136 audited M2134 as a clean six-unit controlled panel.
M2137 designed a no-rerun support-matrix protocol.
M2138 materialized 24 support rows over 6 panel units and 4 profile labels.
M2139 audited the support matrix and identified the missing denominator issue.
M2140 designed a denominator-source inventory.
M2141 materialized 30/30 denominator rows across 6 source kinds and 5 profiles.
M2142 audited that inventory as complete.
M2143 designed denominator-backed descriptive diagnostics.
M2144 materialized 5 profile summaries, 30 source-kind/profile rows, and 6 diagnostic contrasts.
M2145 audited the diagnostics and blocked ranking, paper, finite-window-vs-GRU, and self-ID claims.
```

The loop is technically clean. It has no reset, rollout, training, replay, PPO,
checkpoint promotion, actor-input change, profile-specific tuning, ranking,
winner selection, paper-level claim, finite-window-vs-GRU verdict, or level3
self-ID claim inside the synthesis window.

## Supported Claims

Supported:

```text
The comparison-support generated-proxy branch can produce a complete,
denominator-backed diagnostic comparison artifact with explicit claim
boundaries.
```

Also supported:

```text
The branch is useful as scaffolding: it exercises candidate generation,
materialization, reset validation, measured execution, localization,
qualification, controlled-panel construction, support-matrix materialization,
denominator inventory, and diagnostic comparison materialization.
```

Descriptive generated-proxy rates from M2144:

```text
L0_current_masked:          success 0.0500, collision 0.2500, offtrack 0.7000
L1_one_step:                success 0.0833, collision 0.3000, offtrack 0.6167
L2_window_50:               success 0.0000, collision 0.0000, offtrack 1.0000
L3_online_gru:              success 0.3667, collision 0.1333, offtrack 0.5000
L3_reset_control_corrected: success 0.4333, collision 0.1667, offtrack 0.4000
```

These rates support only route diagnosis. They do not support a controller
ranking.

## Falsified Claims

Falsified or still unsupported:

```text
No paper-level benchmark claim is supported because the rows are generated
comparison-support smoke proxies, not a frozen current-sim paper benchmark.

No controller-family ranking is supported because the branch explicitly blocks
rank and winner fields.

No finite-window-vs-GRU conclusion is supported because the comparison remains
generated-proxy diagnostic evidence and the L3 reset-control row is
descriptively stronger than the online GRU row on success and offtrack rate.

No level3 self-identification claim is supported because no wrong-history,
delayed-history, or matched current-state intervention outcome test is run.
```

The strongest negative signal is:

```text
L3_reset_control_corrected > L3_online_gru on success and offtrack rate in the
M2144 generated-proxy diagnostic artifact.
```

This does not prove reset-control is the final engineering answer, but it does
falsify a naive recurrent-memory interpretation of the generated-proxy branch.

## Failure Taxonomy Summary

No execution failure is active in this window.

The active taxonomy risks are evidence risks:

```text
metric_artifact:
  descriptive profile rates could be mistaken for a ranking.

public_gate_overfit:
  the branch is generated-proxy-only and has been repeatedly shaped through
  public support gates.

contract_interpretation_risk:
  support artifacts could be mistaken for paper-valid active-safety tasks.

self_id_claim_artifact:
  online GRU success could be overinterpreted even though reset-control is
  descriptively stronger in M2144.
```

These risks are controlled by keeping all branch outputs diagnostic-only and
requiring a new branch before paper-route comparison.

## Public Gate Overfit Risk

Risk remains medium-to-high.

Reasons:

```text
the branch uses generated comparison-support smoke proxies;
paper_validity_claim remains false;
private holdout is not used;
the controlled panel has only 6 source-kind units;
the denominator-backed comparison is descriptive and route-facing;
L3 reset-control outperforming L3 online blocks any recurrent-memory claim.
```

The branch has done its job as scaffolding. Continuing to refine this same
generated-proxy panel would likely increase local-process confidence without
materially improving the paper verdict.

## Next Branch Decision

Decision: `pivot`.

Reason:

```text
M2136-M2145 completed a clean diagnostic loop, but the evidence is still
generated-proxy-only and cannot support ranking, paper-level comparison,
finite-window-vs-GRU verdicts, or level3 self-ID. The next evidence increment
must move from scaffolding toward a frozen current-simulator controlled
comparison benchmark design.
```

Immediate next milestone:

```text
m2147-paper-route-current-sim-controlled-comparison-benchmark-design
```

M2147 should design the benchmark route, not run it. The design must align with
the paper-route plans:

```text
compare L0/L1/L2/L3 families fairly;
use the same deployable actor input and actuator-level action contract;
separate engineering driver performance from recurrent-belief or self-ID claims;
include current-response, finite-window, online-GRU, and reset/truncated controls;
define task families before measuring;
keep high-fidelity simulation as later validation, not the current blocker.
```

The generated-proxy branch is closed as a successful scaffolding branch and a
negative mechanism-warning branch. It should not be extended with more
process-only denominator or support-matrix milestones.
