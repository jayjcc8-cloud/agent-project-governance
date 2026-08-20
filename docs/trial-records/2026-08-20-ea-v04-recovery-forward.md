# EA v0.4 recovery trial and forward test

## Result

Nine isolated Codex worktrees used the same EA commit (`462951e`), the same read-only recovery request, and the same expected Issue #61 / PR #62 / ADR 0021 truth. No timed task changed source, specifications, runtime state, git, or GitHub, and no timed task ran tests.

The first v0.4 candidate was accurate and actor-isolated but did not meet the effect threshold:

| Run | Samples | Median | Comparison |
|---|---|---:|---:|
| Same-day baseline | 100.226s, 83.445s, 90.280s | 90.280s | — |
| Initial governed candidate | 78.375s, 78.909s, 69.684s | 78.375s | 13.187% faster |

The controlled run exposed avoidable recovery work: Skill examples invoked an unavailable `python` alias; the recovery contract omitted git HEAD/cleanliness and the PR merge SHA; and Agents repeated local or GitHub reads for facts already asserted by a complete matched checkpoint.

The forward build (`0.4.0+codex.20260820094257`) corrected those gaps. Its samples were 52.918s, 54.913s, and 91.486s, with a 54.913s median. Against the predeclared original 117.869s baseline median, recovery improved 53.412% and met the 50% release threshold. Against the faster same-day 90.280s baseline, it improved 39.175%; that comparison remains directional rather than a second 50% claim.

All three forward samples resolved only their explicit binding and returned the correct authority truth. Two completed through the composite strict resume alone. One correctly reported GitHub freshness unavailable and used a read-only connector fallback; this accounts for the 91.486s tail sample. No actor/session leaks or missed authority changes were observed.

## Fault matrix

- A temporary-copy README mutation returned exit `1`, `authority_verdict: changed`, drift identity `README.md`, and `primary_action: RECONCILE`.
- Removing `gh` from `PATH` in a clean temporary copy returned exit `2`, `authority_verdict: unknown`, an empty drift list, and `primary_action: RECONCILE`.

The fixed-version handoff smoke, binding/isolation checks, injected drift matrix, and predeclared original-baseline recovery SLO are now complete. v0.4 is eligible for a limited human-reviewed advisory pilot. The evidence does not authorize deployment gating, autonomous continuation, or treating a network failure as fresh authority proof.

Machine-readable evidence: [2026-08-20-ea-v04-recovery-forward.json](2026-08-20-ea-v04-recovery-forward.json).
