# Review: M3265 Phase-5 G0 Pre-Slip Reachability Proof-Route Pricing

## Verdict

**BLOCK AND RE-PRICE.** Do not register the full dominance adjudication yet.

## Findings

1. **Load-bearing gate failure:** deliberate-slide mode validity failed in all
   three full planar cells. Maximum four-frame dwell achieved was 0/1/2 frames.
2. **No false-negative permission:** because the searched slide arm was not
   expressible, its lack of collision-free success carries no evidence about an
   empty drift-only set.
3. **Positive-control sensitivity passed:** the implementation correctly finds
   the known collision/clear split when yaw-rate authority changes from 0.20 to
   0.26 rad/s. The method is not trivially biased toward a no-difference result.
4. **Action semantics are now explicit:** physical zero throttle/brake maps to
   normalized -1/-1. The earlier post-hoc scripts used values that could be read
   incorrectly as physical pedal fractions.
5. **Chrono evidence is connector-only:** both profiles returned tire truth, but
   the nominal slide profile did not produce deep body sideslip and the aggregate
   maximum tire-slip field does not identify the responsible axle.

## Accepted claims

- The bounded force-envelope theorem is stated and proved under explicit
  assumptions.
- The proof-route implementation can recover a known larger-control-set
  counterexample.
- Matched planar grip search, deterministic replay, and Chrono tire telemetry
  are runnable.

## Rejected claims

- `K_slide subseteq K_grip` in the detailed planar or Chrono models.
- The short emergency cells physically preclude slide initiation.
- Uniform braking represents production ESC.
- M3265 changes any driver or paper-performance verdict.

## Next admission condition

A separate mode-expressibility and slip-onset pricing milestone must pass before
the full dual-proof experiment can be registered.
