# AGENTS.md
## Operational Directives
1. **Persistence:** You are stateless between turns. You MUST read `CURRENT_STATE.md` at the start of every interaction.
2. **Async Only:** All tasks >60s must use `safe_run.sh`.
3. **Validation:** Never assume a file exists. Run `ls -F` first.
4. **No Hallucination:** If a tool fails, stop and log it. Do not invent a success.
