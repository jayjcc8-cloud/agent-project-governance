# APG trial and value-evaluation records

## V1 product-value window

APG V1 is accepted through evidence from real product work, not from mechanism operation alone. Use [the three-real-task value evaluation](apg-v1-three-task-value-evaluation.md) for the initial observation window.

The V1 record separates APG evidence from knowledge reuse, requires a concrete `APG_IMPACT`, and forbids `APG_ACCEPTANCE=PASS` unless APG solved or avoided a specific continuity/context problem without blocking product development. ADG and drift governance are not part of this acceptance window.

## Historical mechanism template

The template below and existing records are retained as historical mechanism evidence. They may validate checkpoint behavior, timing, isolation, compatibility, or declared-source change handling, but they are not the APG V1 product definition or primary acceptance criteria.

Use one copy per governed trial and one comparable run without the plugin. Do not record chat transcripts, secrets, or source-file contents.

## Setup

- Date:
- Project and feature:
- Participant/agent configuration:
- Plugin version:
- Spec Kit / Superpowers / bridge versions:
- Governed or baseline run:

## Outcomes

- Recovery time after compaction, crash, or new session:
- Actor state leaks observed:
- Authority changes missed before continuation:
- Work units resumed successfully:
- Manual reconciliation events:

## Evidence and conclusion

- Relevant state paths, commands, and test results:
- Failures or ambiguity:
- Did governance materially improve recovery time or reduce leaks/drift?
- Recommended product change:

Calculate each paired run with the same declared threshold:

```bash
python3 skills/context-governance/scripts/trial_summary.py \
  --baseline 116.522 --baseline 115.979 --baseline 144.616 \
  --governed 66.787 --governed 57.059 --governed 88.413 \
  --threshold-percent 50 \
  --json
```

Keep raw durations and the JSON result with the trial evidence. A `directional_benefit` verdict is not equivalent to meeting the effect threshold.

Recorded historical trials:

- [2026-08-13 EA Issue #61 / PR #62 paired recovery](trial-records/2026-08-13-ea-pr62-paired.md) — accuracy and isolation passed; recovery-time effect was not demonstrated.
- [2026-08-20 pinned handoff compatibility smoke](trial-records/2026-08-20-pinned-handoff-smoke.md) — exact dependency, handoff, and governance lifecycle gates passed; macOS and cache-retention limits were exposed.
- [2026-08-20 EA v0.4 recovery trial and forward test](trial-records/2026-08-20-ea-v04-recovery-forward.md) — binding/isolation and drift checks passed; the predeclared original-baseline recovery SLO passed at 53.412%, while the same-day comparison remained directional at 39.175%.
