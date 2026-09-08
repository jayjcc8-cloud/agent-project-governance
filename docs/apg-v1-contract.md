# RepoKeel V1 core contract

This canonical contract supersedes the pre-shrink APG V1 process for future tasks.
The filename and existing readers remain compatible. Historical records are not
rewritten or migrated. Decision: [EA #176 three-task closeout](https://github.com/jayjcc8-cloud/ea-quant/issues/176#issuecomment-5578482298), `REPOKEEL_DECISION=SHRINK`.

## Core loop

`RETRIEVE -> EXECUTE -> CONDITIONAL_LEARN`

A normal task has exactly two required RepoKeel actions:

1. At real task start, search once for knowledge directly relevant to the current
   contract, known problem, decision, solution, or reusable method. Use the
   project's approved knowledge route. Do not scan the whole knowledge base.
   Report only `RETRIEVAL_USED=YES|NO` and
   `REUSED_KNOWLEDGE=<references or NONE>` in the existing task conversation.
   No relevant hit means `REUSED_KNOWLEDGE=NONE`; continue immediately.
2. Once the real task is accepted/completed, check `NEW_KNOWLEDGE=YES|NO` and
   `UPDATE_NEEDED=YES|NO`. Only `NEW_KNOWLEDGE=YES` or `UPDATE_NEEDED=YES` permits
   a knowledge write/update through the user's authorized knowledge route.
   Otherwise `KNOWLEDGE_WRITE=SKIPPED` and stop. No empty or routine summary.

Actual product execution and acceptance belong to the project, not RepoKeel.
These checks are brief task observations, not separate files, checkpoint commands,
reports, or proof-of-compliance records. Do not copy Issue/PR/Git/CI facts.
Refine, merge, promote, or convert knowledge to a method, skill, or spec only
when actual reuse in a later real task provides evidence and the project permits it.

## Authority

| Concern | Authority |
|---|---|
| TASK AUTHORITY | GitHub Issue / explicit user task |
| CODE AUTHORITY | Git |
| DELIVERY AUTHORITY | PR + main |
| VERIFICATION | CI / explicit acceptance evidence |
| REPOKEEL AUTHORITY | reusable development knowledge only |

RepoKeel may reference these sources. It does not own product requirements,
Issue/PR lifecycle, risk approval, release status, CI status, or product acceptance.
It must not maintain a second permanent task lifecycle, evidence package, context
manifest, completion report, or knowledge report. Existing evidence is referenced,
not copied into a second source of truth.

## Exceptional recovery

Recovery is event-driven, only for actual context loss, session interruption,
handoff, or resumption of a long-running task. Ordinary continuation, task start,
review verdict, HEAD change, and task completion do not require recovery records.
For a normal uninterrupted task: `RECOVERY_USED=NO` and
`RECOVERY_ARTIFACT_REQUIRED=NO`; neither requires an extra report.

Use `context-governance` only for such an event. Existing actor-owned checkpoints
can be read using the existing CLI. When needed for a real handoff, record only
missing context and links to canonical evidence. No task must initialize, bind,
checkpoint, evaluate, validate, or close a work unit just to use RepoKeel.
An unbound recovery returns to project authorities; do not create empty recovery
state. Optional hooks run only on resume/context loss or compaction of bound work,
never normal startup, subagent lifecycle, or stop.

## Responsibilities and compatibility

The only V1 responsibilities are Retrieve, Learn, Update, and exceptional Recover.
Everything else is out of scope as a RepoKeel obligation. The five existing skill
IDs and explicit compatibility CLI remain available, not a mandatory chain.
Bootstrap and delivery helpers defer to project-owned rules; they add no mandatory
steps, reviewer chain, acceptance layer, or state store.

Old knowledge and runtime records remain readable without migration. Existing
CLI flags, schema versions, and state readers are retained for explicit recovery;
new ordinary tasks produce no runtime state. `.agent-runtime/` is derived recovery
memory, not the knowledge base or project authority.

No new hook bus, schema, database, router, coordinator, telemetry, scoring,
knowledge graph, workflow engine, or automatic knowledge promotion is part of V1.
The completed three-task pilot is decision evidence, not a recurring evaluation
requirement. Do not repeat the pilot or generate per-task APG acceptance reports.
