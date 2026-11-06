# AGENTS.md (instructions for Codex / coding agents)

## Project
GEO tracker for a Vietnamese securities company (CTCK). It measures how ChatGPT mentions and cites the brand, from two sources:
- `codex`: automated. `geo.py codex-run` asks each planned question through an isolated, ephemeral `codex exec` (proxy for ChatGPT web).
- `chatgpt`: a ~20-run manual sample on chatgpt.com, read from the account export `conversations.json`. Used by `calibrate` to measure the proxy gap.

## Hard rules
- **When working as a coding agent in this repo, never answer the measurement questions yourself** and never write or simulate answers into `exports/` or `data/`. Answers come only from `geo.py codex-run` (isolated subprocess) or a real chatgpt.com export.
- Do not automate or scrape the chatgpt.com UI (no Playwright, Selenium, or reverse-engineered endpoints).
- Do not use the OpenAI API for measurement. `codex-run` strips `OPENAI_API_KEY` / `CODEX_API_KEY` and uses the ChatGPT login in a dedicated `CODEX_HOME` (`~/.codex-geo`).
- Keep the isolation flags in `codex_args()` (ephemeral, ignore user config/rules, no AGENTS.md, no shell/memories/apps/plugins, empty temp cwd, live web search).
- Standard library only (no pandas). Keep `geo.py` a single file.
- Code comments in English. User-facing output and reports in Vietnamese.
- Files written for Excel use `utf-8-sig`.

## Layout
- `config/`: brand.json, prompts.csv, entities.csv, source_types.csv, page_types.csv, codex.json, codex_instructions.md
- `exports/<YYYY-MM>/codex/`: raw codex runs (one JSON per run). `exports/<YYYY-MM>/conversations.json`: ChatGPT export. Do not modify.
- `data/<YYYY-MM>/<source>/`: parsed CSVs + entity_candidates.csv. `review/`: human accuracy review. `reports/`: markdown reports.

## Commands
- `python geo.py codex-run --month M [--only Q009] [--limit N]` (resumable, then parses)
- `python geo.py checklist --month M [--sample 20]`
- `python geo.py inspect <export>`, `python geo.py parse <export|codex folder> [--month M]`
- `python geo.py report --month M [--source codex|chatgpt]`, `python geo.py calibrate --month M`
- Test without touching real data: set `GEO_WORKDIR` to a temp dir.

## Formats
- Codex `--json` events: `item.completed` with `item.type == "web_search"` (`action.queries`, `results[].url/ref_id`) and `agent_message` (`text`). Parsed by `extract_codex()`.
- ChatGPT export: `extract_run()` (content_references / citations, search_result_groups, search_queries). Adapt from `inspect` output.
