# M2145 Paper-Route Outcome-Supported Decisive Comparison-Support Denominator-Backed Comparison Result Audit

- status: completed
- decision: `denominator_backed_diagnostic_comparison_audit_route_to_post_diagnostic_synthesis`
- manifest: `experiments/manifests/m2145-paper-route-outcome-supported-decisive-comparison-support-denominator-backed-comparison-result-audit.json`
- audited summary: `runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/summary.json`
- reset/rollout/measured execution in M2145: `false`
- policy actions executed in M2145: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2144 is a clean denominator-backed diagnostic comparison materialization:

```text
result_class: comparison_support_denominator_backed_diagnostic_comparison_pass
profile_count: 5
source_kind_count: 6
denominator_row_count: 30
diagnostic_contrast_row_count: 6
blocked_verdict_field_count: 0
claim_boundary_violation_count: 0
guardrail_violation_count: 0
```

The materialization preserves the intended boundary. It writes descriptive
profile rates, source-kind/profile rows, and pre-registered diagnostic deltas
only. It does not rank profiles, choose a winner, issue a paper result, compare
finite-window against GRU as a verdict, or test level3 self-identification.

## Descriptive Diagnostics

Profile-level descriptive rates over the complete M2141 denominator inventory:

```text
L0_current_masked:          success 0.0500, collision 0.2500, offtrack 0.7000
L1_one_step:                success 0.0833, collision 0.3000, offtrack 0.6167
L2_window_50:               success 0.0000, collision 0.0000, offtrack 1.0000
L3_online_gru:              success 0.3667, collision 0.1333, offtrack 0.5000
L3_reset_control_corrected: success 0.4333, collision 0.1667, offtrack 0.4000
```

Pre-registered diagnostic contrasts:

```text
L1 - L0:          success +0.0333, collision +0.0500, offtrack -0.0833
L2 - L1:          success -0.0833, collision -0.3000, offtrack +0.3833
L3 online - L1:   success +0.2833, collision -0.1667, offtrack -0.1167
L3 online - L2:   success +0.3667, collision +0.1333, offtrack -0.5000
L3 reset - online:success +0.0667, collision +0.0333, offtrack -0.1000
L3 reset - L2:    success +0.4333, collision +0.1667, offtrack -0.6000
```

These rows are useful for route diagnosis only. Every contrast row keeps
`verdict_allowed=false`, `ranking_allowed=false`, `paper_claim_allowed=false`,
and `self_id_claim_allowed=false`.

## Interpretation Boundary

Supported:

```text
The comparison-support branch now has a denominator-backed diagnostic comparison
artifact over all 5 measured profiles and all 6 controlled panel source kinds.
```

Also supported:

```text
On this generated-proxy diagnostic panel, the L3-family profiles have higher
descriptive success rates than L0, L1, and L2.
```

Still unsupported:

```text
No controller-family ranking is supported.
No winner is selected.
No paper-level benchmark claim is supported.
No finite-window-vs-GRU verdict is supported.
No level3 self-identification claim is supported.
```

The reset-control row is especially important:

```text
L3_reset_control_corrected is descriptively stronger than L3_online_gru on
success and offtrack rate in this artifact.
```

Therefore M2144 cannot be used as recurrent-memory or belief-state evidence.
It actually blocks any naive claim that the online GRU profile is stronger
because of recurrent history on this generated-proxy panel.

## Route Decision

The diagnostic artifact is clean enough to support a bounded route decision, but
it is not clean enough to support another profile-comparison claim. The next
step should be branch synthesis, not another local process milestone.

Immediate next milestone:

```text
m2146-paper-route-outcome-supported-decisive-comparison-support-post-diagnostic-synthesis
```

M2146 should synthesize the M2136-M2145 post-M2135 diagnostic loop and decide
whether to continue, pivot, stop, or promote to a new branch. It must preserve
the generated-proxy claim boundary and the reset-control negative signal.
