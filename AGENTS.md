# AGENTS.md
## Operational Directives
1. **Persistence:** You are stateless between turns. You MUST read `CURRENT_STATE.md` at the start of every interaction.
2. **Async Only:** All tasks >60s must use `safe_run.sh`.
3. **Validation:** Never assume a file exists. Run `ls -F` first.
4. **No Hallucination:** If a tool fails, stop and log it. Do not invent a success.

## Penfield Memory Protocol

You have access to a persistent memory system (Penfield). Use it to avoid repeating past failures and to contribute findings for future agents.

### On Session START — always do this first:
```bash
penfield_search "VLIW optimization results"      # search for relevant past work
penfield_search "[your mission name] previous"   # check if this was attempted before
```
Read the results. If past work exists, build on it. Do not repeat experiments that already have answers.

### On Session END — always do this last:
Before submitting, write your key findings to Penfield:
```bash
penfield_store "[Mission: CODE_AUDIT_TERRAIN_REFACTOR] RESULT: Found 3 bugs in terrain.rs (lines 47, 112, 203). Fixed all. Added 12 tests. Coverage: 87%. NEXT_AGENT: Focus on urban.rs which has no tests."
```
Rules for storing:
- Include mission name, repo, and date in the content
- Include the most important numerical results
- Include a NEXT_AGENT: line telling the next session what to focus on
- Tag with mission type: audit, survey, refactor, test, etc.

### During the Session — store milestones:
When you find something significant (a bug, a record result, a surprising failure), store it immediately:
```bash
penfield_store "[FINDING] terrain.rs line 47: off-by-one in boundary calculation causes wrap-around at edge tiles."
```

## Penfield Tool Reference
- Search: `penfield_search "<query>"` — returns relevant past memories
- Store: `penfield_store "<content>"` — saves a memory for future agents
- Both tools are available in your shell environment as executable scripts.
